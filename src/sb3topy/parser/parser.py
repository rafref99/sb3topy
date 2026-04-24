"""
parser.py

Orchestrates the job of parsing the project.json
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from .. import config
from . import sanitizer, specmap, targets, linter, ast_generator
from .specmap import codemap
from .variables import Variables

__all__ = ('parse_project', 'Parser')

logger = logging.getLogger(__name__)


def parse_project(project, manifest, parser_config=None):
    """Parses project and returns the Python code"""
    logger.info("Compiling project into Python...")
    Variables.reset()
    targets.Target.broadcasts = {}
    targets.Target.cloned_targets = set()
    return Parser(project, manifest, parser_config).parse()


class Parser:
    """
    Handles parsing a target

    Attributes:
        targets: A Targets instance used to handle each target in the
            sb3 project.json.

        project: A dict like object containing the data from the sb3
            project.json.
    """

    def __init__(self, project, manifest, parser_config=None):
        self.config = parser_config or config.snapshot_config()
        self.targets = targets.Targets(self.config)
        self.manifest = manifest
        self.project = project

    def parse(self):
        """Parses the sb3 and returns Python code"""
        # Run pre-conversion analysis
        results = linter.lint_project(self.project.json)
        for warning in results['warnings']:
            logger.warning("Linter: %s", warning['message'])

        # Run the first parsing pass
        self.first_pass()

        # Run the second parsing pass
        self.second_pass()

        # Run the final parsing pass
        return self.third_pass()

    def first_pass(self):
        """
        Runs the first pass of the parser.
        The first pass creates classes for targets and prototypes,
        and marks universal variable used in sensing_of.
        """
        logger.info("Initializing parser...")

        # Create a class for each target
        self.targets.add_targets(self.project['targets'])

        # Have each target run a first pass
        for target in self.targets:
            target.first_pass()

    def second_pass(self):
        """
        Runs the second pass of the parser.

        Creates classes for each Variable and runs type
        guessing for variables and procedure arguments.

        Also names solo broadcast receivers.
        """
        logger.info("Running optimizations...")

        for target in self.targets:
            target.second_pass()

        # Guess the type of each variable
        if self.config.VAR_TYPES:
            self.targets.digraph.resolve()

        # Name solo broadcast receivers
        broadcasts = targets.Target.broadcasts
        for broadcast, target_name in broadcasts.items():
            if target_name is not None:
                target = self.targets.targets[target_name]
                target.events.name_hat("broadcast_{BROADCAST}", {
                    'BROADCAST': broadcast})

    def third_pass(self):
        """
        Runs the third pass of the parser.
        This pass actually creates the Python code for the project.
        """
        logger.info("Generating Python code...")

        code = codemap.file_header() + "\n\n\n"

        for target in self.targets:
            self.target = target
            code = code + self.parse_target(target) + "\n\n\n"

        # Parse monitors
        monitors_code = codemap.parse_monitors(
            self.project.get('monitors', []), self.targets)

        code = code + "\n\n" + codemap.file_footer(monitors_code) + "\n"

        return code

    def parse_target(self, target: targets.Target):
        """Converts a sb3 target dict into the code for a Python class"""

        # Get property definitions, class description, etc.
        header_code = codemap.create_header(target) + "\n\n"

        # Parse variables, lists, costumes, and sounds
        init_code = codemap.create_init(target, self.manifest) + "\n\n"

        # Parse all blocks into code
        block_code = self.parse_blocks()

        # Indent init and block code
        code = header_code + init_code + block_code

        # Return the final code for the class
        return codemap.target_class(code, target['name'], target.clean_name)

    def parse_blocks(self):
        """Creates a function for each topLevel hat in self.target.blocks"""
        # Parse all topLevel blocks into code
        code = []
        for blockid, block in self.target.hats:
            code.append(self.parse_hat(blockid, block))

        return '\n\n'.join(code)

    def parse_hat(self, blockid, block):
        """Gets the code if any, for a topLevel block"""

        # Verify the block is a known hat
        if specmap.is_hat(block):
            stack = self.parse_stack(blockid)
            return stack[1]

        # TODO Add hats to identifiers

        logger.debug("Skipping topLevel block '%s' with opcode '%s'",
                     blockid, block['opcode'])
        return ""

    def parse_stack(self, blockid: str, parent_block: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        Parses a stack/input into Python code using AST-based generation.
        """

        ast_gen = ast_generator.ASTGenerator()
        block = self.target.blocks[blockid]
        last_blockmap = None

        while block:
            # Get the conversion map
            blockmap = specmap.get_blockmap(block, self.target)
            last_blockmap = blockmap

            # Get fields
            args = {}
            for name in block['fields']:
                args[name] = 'field', block['fields'][name]

            # Get inputs
            for name, value in block['inputs'].items():
                args[name] = specmap.parse_input(self.target.blocks, value)

            # Parse each argument using the blockmap
            clean_args = {}
            for name, end_type in blockmap.args.items():
                clean_args[name] = self.parse_arg(name, args, end_type, block)
                if not isinstance(clean_args[name], str):
                    raise TypeError(
                        f"Parsed arg '{name}' for opcode "
                        f"'{block['opcode']}' must be str, got "
                        f"{type(clean_args[name]).__name__}")

            # Create the code for the block
            # For now, we still use the formatted string but parse it into AST
            # This allows us to gradually transition while improving robustness.
            formatted_code = blockmap.format_code(clean_args)
            ast_gen.add_statement(formatted_code)

            # Get the next block
            block = self.target.blocks.get(block['next'])

        # If the parent block is a loop, yield
        if parent_block and specmap.is_loop(parent_block) and \
            last_blockmap and last_blockmap.return_type == 'stack' and not \
                (self.target.prototype and self.target.prototype.warp):
            ast_gen.add_statement(codemap.yield_())

        # At the end of a procedure definition, clear the target's prototype
        if parent_block and specmap.is_procedure(parent_block):
            self.target.prototype = None

        # Determine the return type of the stack (from the last block)
        return_type = last_blockmap.return_type if last_blockmap else 'stack'

        # Get the compiled code from the AST generator
        code = ast_gen.get_code()

        return return_type, code.strip()

    def parse_arg(self, name, args, end_type, block):
        """
        Ensures the type of an input matches
        the type expected by the blockmap.

        Returns an AST node representing the argument.
        """

        # Get the unparsed value and type from args
        start_type, value = args.get(name, ('none', "None"))

        # An unparsed block
        if start_type == 'blockid':
            start_type, value = self.parse_stack(value, block)

        # A variable reporter
        elif start_type == 'variable':
            # Identify variable by its name
            # If the variable exists, get its type and reference
            start_type = self.target.vars.get_type('var', value)
            value = self.target.vars.get_reference('var', value)

        # A list reporter
        elif start_type == 'list_reporter':
            start_type = 'block'
            value = self.target.vars.get_reference('list', value) + '.join()'

        # Directly cast a literal
        if start_type == 'literal':
            if end_type == 'field':
                value = self.parse_field(value, end_type, args)
            else:
                value = sanitizer.cast_literal(value, end_type)
        elif start_type == 'field':
            # Fields take special parsing
            value = self.parse_field(value, end_type, args)
        else:
            # Put a runtime cast wrapper around a block
            value = sanitizer.cast_wrapper(value, start_type, end_type)

        # If the start_type is 'stack', we should not attempt to parse it as an expression
        if start_type == 'stack':
            # For stacks, we return the value directly.
            # In the future, we should probably return a list of AST nodes.
            return value

        # Verify the result is valid Python, but keep the original string.
        # ast.unparse() can remove outer parentheses that are meaningful once
        # this expression is embedded into a larger Scratch expression.
        ast_generator.expression_to_ast(value)
        return value

    def parse_field(self, value, end_type, args):
        """
        Parses a field depending on the value of end_type.

        If end_type is 'field', the value will be lowered and quoted.

        If end_type is 'variable', the value will
        be converted into a variable identifier.

        If end_type is 'list', the value will
        be converted into a list identifier.

        If end_type is 'property', the value will
        be converted into a universal identifier.

        If end_type is 'hat_ident', the value will
        be converted into a function identifier.

        Otherwise, the value will be quoted and a warning shown.
        """
        # Resolve the variable/list name if it's an ID
        if end_type in ('variable', 'list'):
            # The value could be [name, id] or just name/id
            if isinstance(value, (list, tuple)):
                value = value[1] if len(value) > 1 else value[0]
        elif isinstance(value, (list, tuple)):
            value = value[0]

        # Quote and lower a field
        if end_type == 'field':
            return sanitizer.quote_field(value.lower())

        # Get a variable identifier
        if end_type == 'variable':
            return self.target.vars.get_reference('var', value)

        # Get a list identifier
        if end_type == 'list':
            return self.target.vars.get_reference('list', value)

        # Get a universal variable identifier
        if end_type == 'property':
            return Variables.get_universal(value)

        # Create a hat identifier
        if end_type == 'hat_ident':
            return self.target.events.name_hat(
                value, {name: val[1] for name, val in args.items()})

        # Get an existing hat identifier for another target
        if end_type == 'ex_hat_ident':
            target_name = args['TARGET'][1]
            if isinstance(target_name, (list, tuple)):
                target_name = target_name[0]
            return self.targets.targets[
                target_name].events.existing_hat(
                    value, {
                        name: val[1][0] if isinstance(val[1], (list, tuple)) else val[1]
                        for name, val in args.items()
                    })

        # Get a procedure argument identifier
        if end_type == 'proc_arg':
            return self.target.prototype.get_arg(value)

        # Default to quoting
        logger.warning("Unknown field type '%s'", end_type)
        return sanitizer.quote_field(value)
