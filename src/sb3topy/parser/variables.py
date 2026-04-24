"""
variables.py

Handles variable naming and interfaces with the typing module to create
type Nodes to determine variable types.

TODO Are names such as 'x position' are still marked as universals?
"""

import logging
from typing import Dict

from .. import config
from . import sanitizer, specmap, typing
from .naming import Identifiers

logger = logging.getLogger(__name__)


def _has_prefix(name: str, prefix: str) -> bool:
    """Return whether a generated variable name already has prefix_."""
    return not prefix or name == prefix or name.startswith(prefix + '_')


def _field_id_or_name(field):
    """Return the Scratch ID from a field tuple/list when available."""
    if isinstance(field, (list, tuple)):
        return field[1] if len(field) > 1 else field[0]
    return field


class Variable:
    """
    Represents a variable or list

    Attributes:
        clean_name: The clean identifier for the variable

        node: The digraph node used to get the type of the variable

        is_changed: Whether the change var by block is used on the
            variable

        is_modified: Whether the list is modified in any way

        is_indexed: Whether the item # of list or contains block is
            used on the list
    """

    def __init__(self, clean_name, node):
        self.clean_name = clean_name

        self.node: typing.Node = node

        self.is_changed = False
        self.is_modified = False
        self.is_indexed = False

    def mark_set(self, to_type):
        """Mark the variable as being set to a value of to_type"""
        self.node.add_type(to_type)

    def mark_changed(self):
        """Mark the varable as modified by the change by block"""
        self.is_changed = True
        self.node.add_type('int')

    def mark_modified(self):
        """Marks a list as modified by a block (not static/a constant)"""
        self.is_modified = True

    def mark_indexed(self):
        """Marks a list a indexed by a item # of or contains block"""
        self.is_indexed = True

    def get_type(self):
        """Gets the type of a variable"""
        # Force the type to be numeric if changed
        if self.is_changed and config.CHANGED_NUM_CAST:
            # Decide between int and float
            if self.node.known_type == 'int':
                return 'int'
            return 'float'

        # Otherwise, use the detected type
        return self.node.known_type

    def get_list_type(self):
        """Gets the class which should be used for a list"""
        if config.LIST_TYPES and not self.is_modified:
            return "StaticList"
        return "List"


class Variables:
    """
    Handles variable and list naming for a target.

    Class Attributes:
        global_vars: Identifiers instance used to name and contain
            variables owned by the stage

    universal_vars: Identifiers instance used to contain variable
            names which should be kept consistent across sprites, such
            as those used in the sensing_of block.

        all_ids: Scratch variable/list IDs seen anywhere in the project.
            This is a fallback for copied scripts that keep an ID from
            another sprite but no longer declare that variable locally.

    Attributes:
        local_vars: Identifiers instance used to name and contain
            variables for this sprite

    All universal variables must be marked before variables are added.
    """

    global_vars: Identifiers = None
    universal_vars: Identifiers = None
    global_ids: Dict[str, str] = {}
    all_ids: Dict[str, str] = {}

    @classmethod
    def reset(cls):
        """Reset project-scoped variable registries before parsing a project."""
        cls.global_vars = None
        cls.universal_vars = None
        cls.global_ids = {}
        cls.all_ids = {}

    def __init__(self, target_name, is_stage):
        # Initialize class attributes
        if self.global_vars is None:
            Variables.global_vars = Identifiers()
            Variables.universal_vars = Identifiers()
            Variables.global_ids = {}
            Variables.all_ids = {}

        if is_stage:
            self.local_vars = self.global_vars
            self.local_ids = self.global_ids
        else:
            self.local_vars = Identifiers()
            self.local_ids = {}
        self.digraph = None

        # Save for creating tuple_ids
        self.target_name = target_name

    def second_pass(self, target, digraph):
        """
        Parses the variables in a target

        Should not be called until a Variables
        instance has been created for every target
        """

        self.digraph = digraph

        # Update universal names
        self.local_vars.set.update(self.universal_vars.set)

        # Read variables
        for varid, (name, value, *_) in target['variables'].items():
            self.create_local("var", name, digraph, value)
            self.local_ids[varid] = name
            self.all_ids.setdefault(varid, name)

        # Read lists
        for listid, (name, values) in target['lists'].items():
            self.create_local('list', name, digraph, values)
            self.local_ids[listid] = name
            self.all_ids.setdefault(listid, name)

    def get_reference(self, prefix, name):
        """
        Gets a variable reference,
        eg. self.var_x or util.sprites.stage.var_x
        """
        # Resolve ID if necessary
        if name in self.local_ids:
            name = self.local_ids[name]
        elif name in self.global_ids:
            name = self.global_ids[name]
        elif name in self.all_ids:
            name = self.all_ids[name]

        # Ensure the name starts with the prefix
        if not _has_prefix(name, prefix):
            name = prefix + '_' + name

        # Check if a local variable exists with the name
        if name in self.local_vars.dict:
            return "self." + self.local_vars.dict[name].clean_name

        # Check if a global variable exists with the name
        if name in self.global_vars.dict:
            return "util.sprites.stage." + self.global_vars.dict[name].clean_name

        # This should not occur, but can be handled
        logger.warning("Unregistered var ref '%s'", name)

        # Create a new local variable
        return "self." + self.create_local('', name, typing.DiGraph()).clean_name

    def get_type(self, prefix, name):
        """
        Gets the type for a global or local variable
        """
        # Resolve ID if necessary
        if name in self.local_ids:
            name = self.local_ids[name]
        elif name in self.global_ids:
            name = self.global_ids[name]
        elif name in self.all_ids:
            name = self.all_ids[name]

        # Ensure the name starts with the prefix
        if not _has_prefix(name, prefix):
            name = prefix + '_' + name

        # Check if a local variable exists with the name
        if name in self.local_vars.dict:
            return self.local_vars.dict[name].get_type()

        # Check if a global variable exists with the name
        if name in self.global_vars.dict:
            return self.global_vars.dict[name].get_type()

        # This should not occur, but can be handled
        logger.warning("Unregistered var type '%s'", name)

        # Create a new local variable
        return self.create_local('', name, typing.DiGraph()).get_type()

    def get_local(self, prefix, name) -> str:
        """
        Gets the identifier for a local variable
        No self. prefix is added.
        """
        # Resolve ID if necessary
        if name in self.local_ids:
            name = self.local_ids[name]
        elif name in self.all_ids:
            name = self.all_ids[name]

        # Ensure the name starts with the prefix
        if not _has_prefix(name, prefix):
            name = prefix + '_' + name

        # Check if a local variable exists with the name
        if name in self.local_vars.dict:
            return self.local_vars.dict[name].clean_name

        # This should not normally occur, but can be handled
        logger.warning("Unregistered local var '%s'", name)

        # Create a new local variable
        return self.create_local(prefix, name, typing.DiGraph()).clean_name

    def get_var(self, prefix, name) -> Variable:
        """
        Gets a Variable object, either global or local
        """
        used_project_id_fallback = False
        # Resolve ID if necessary
        if name in self.local_ids:
            name = self.local_ids[name]
        elif name in self.global_ids:
            name = self.global_ids[name]
        elif name in self.all_ids:
            name = self.all_ids[name]
            used_project_id_fallback = True

        # Ensure the name starts with the prefix
        if not _has_prefix(name, prefix):
            name = prefix + '_' + name

        # Check if a local variable exists with the name
        if name in self.local_vars.dict:
            return self.local_vars.dict[name]

        # Check if a global variable exists with the name
        if name in self.global_vars.dict:
            return self.global_vars.dict[name]

        # This should not normally occur, but can be handled
        if not used_project_id_fallback:
            logger.warning("Unregistered var '%s'", name)

        # Create a new local variable
        return self.create_local(prefix, name, self.digraph or typing.DiGraph())

    def create_local(self, prefix, name, digraph, initial_value=None):
        """Creates a safe identifier name"""
        # Ensure the name starts with the prefix
        if not _has_prefix(name, prefix):
            name = prefix + '_' + name

        # Verify the variable doesn't already exist
        if name in self.local_vars.dict:
            # TODO Identify variables with their id as well
            # Sometimes a variable has an invisible duplicate in the json
            # Once fixed, the below should be changed back to warning
            logger.debug("Duplicate local var '%s'", name)

            # Get the type node for the variable
            node = self.local_vars.dict[name].node

            # Add initial value types to the type node
            if initial_value is not None:
                if prefix == 'var':
                    node.add_type(specmap.get_literal_type(initial_value))
                elif prefix == 'list':
                    for value in initial_value:
                        node.add_type(specmap.get_literal_type(value))

            return self.local_vars.dict[name]

        # Create a type node for the variable
        node = digraph.add_node((prefix, self.target_name, name))

        # Add initial value types to the type node
        if initial_value is not None:
            if prefix == 'var':
                node.add_type(specmap.get_literal_type(initial_value))
            elif prefix == 'list':
                for value in initial_value:
                    node.add_type(specmap.get_literal_type(value))

        # Check if a universal identifier already exists
        if name in self.universal_vars.dict:
            # Get the universal identifier
            ident = self.universal_vars.dict[name]

            # Save the identifier
            self.local_vars.dict[name] = Variable(ident, node)

            logger.debug(
                "Creating local var '%s' as universal '%s'", name, ident)

            return self.local_vars.dict[name]

        # Remove invalid characters
        ident = sanitizer.clean_identifier(name)

        # Ensure the identifier is unique
        ident = self.local_vars.suffix(ident)

        # Save the identifier for future use
        self.local_vars.dict[name] = Variable(ident, node)

        logger.debug("Creating local var '%s' as '%s'", name, ident)

        return self.local_vars.dict[name]

    @classmethod
    def mark_universal(cls, name):
        """Saves a name as a universal identifier"""
        # Ensure the name starts with the prefix
        if not _has_prefix(name, 'var'):
            name = 'var' + '_' + name

        # Verify the name isn't already marked
        if name in cls.universal_vars.dict:
            return cls.universal_vars.dict[name]

        # Remove invalid characters
        ident = sanitizer.clean_identifier(name)

        # Ensure the identifier is unique
        ident = cls.universal_vars.suffix(ident)

        # Save the identifier for future use
        cls.universal_vars.dict[name] = ident

        logger.debug("Created universal var '%s' as '%s'", name, ident)

        return ident

    @classmethod
    def get_universal(cls, name):
        """Gets a universal identifier from a name"""
        # Ensure the name starts with the prefix
        if not _has_prefix(name, 'var'):
            name = 'var_' + name

        # Get the universal identifier
        ident = cls.universal_vars.dict.get(name)

        if ident is None:
            logger.error("Unmarked universal var '%s'", name)
            ident = cls.mark_universal(name)

        return ident

    def mark_set(self, target, block):
        """Parses a data_setvariableto block for type guessing"""
        input_type = specmap.get_input_type(
            target, block['inputs']['VALUE'])
        self.get_var(
            'var',
            _field_id_or_name(block['fields']['VARIABLE'])
        ).mark_set(input_type)

    def mark_changed(self, block):
        """Parses a data_changevariableby block for type guessing """
        self.get_var(
            'var',
            _field_id_or_name(block['fields']['VARIABLE'])
        ).mark_changed()

    def mark_modified(self, target, block):
        """Marks a list as modified by block"""
        var = self.get_var('list', _field_id_or_name(block['fields']['LIST']))
        var.mark_modified()

        if block['opcode'] in ('data_addtolist', 'data_insertatlist',
                               'data_replaceitemoflist'):
            input_type = specmap.get_input_type(
                target, block['inputs']['ITEM'])
            var.mark_set(input_type)

    def mark_indexed(self, block):
        """Marks a list as indexed by block"""
        self.get_var(
            'list',
            _field_id_or_name(block['fields']['LIST'])
        ).mark_indexed()
