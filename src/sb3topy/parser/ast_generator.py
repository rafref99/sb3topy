"""
ast_generator.py

Contains the ASTGenerator class for generating Python code from Scratch blocks
using the ast module.
"""

import ast
import logging
from typing import List

logger = logging.getLogger(__name__)


class ASTGenerator:
    """
    Handles the conversion of Scratch blocks to Python AST nodes.
    """

    def __init__(self):
        self.nodes = []
        self.source = []

    @staticmethod
    def parse_expression(code: str) -> ast.AST:
        """Parses a string expression into an AST node."""
        code_strip = code.strip()
        try:
            # If it's multiple lines or looks like a statement,
            # it might still be intended as an expression if it's a single block.
            # But for safety, we try 'eval' first.
            return ast.parse(code_strip, mode='eval').body
        except SyntaxError:
            # If eval fails, try parsing as exec and see if it's a single expression statement
            try:
                tree = ast.parse(code_strip)
                if len(tree.body) == 1:
                    if isinstance(tree.body[0], ast.Expr):
                        return tree.body[0].value
                    if isinstance(tree.body[0], (ast.Pass, ast.Continue, ast.Break)):
                        return tree.body[0]

                # If it's more than one statement, it's not a simple expression.
                # We return it as-is for now, but this is a sign of a logic error in the caller.
                if code_strip != "pass":
                    logger.warning("Code is not a simple expression: %s", code)
                return ast.Constant(value=code)
            except SyntaxError as e:
                logger.error("Failed to parse expression: %s\nCode: %s", e, code)
                return ast.Constant(value=None)

    @staticmethod
    def parse_statement(code: str) -> List[ast.stmt]:
        """Parses a string statement into a list of AST nodes."""
        try:
            # Handle empty or whitespace-only code
            if not code.strip():
                return [ast.Pass()]

            tree = ast.parse(code)
            return tree.body
        except SyntaxError as e:
            logger.error("Failed to parse statement: %s\nCode: %s", e, code)
            return [ast.Expr(value=ast.Constant(value=f"Error: {e}"))]

    def add_statement(self, code: str):
        """Adds a statement to the current list of nodes."""
        self.nodes.extend(self.parse_statement(code))
        if code.strip():
            self.source.append(code)

    def get_code(self) -> str:
        """Returns the generated Python code as a string."""
        if not self.source:
            return ""

        return "\n".join(self.source)


def expression_to_ast(code: str) -> ast.AST:
    """Convenience function for parsing expression strings."""
    return ASTGenerator.parse_expression(code)


def statement_to_ast(code: str) -> List[ast.stmt]:
    """Convenience function for parsing statement strings."""
    return ASTGenerator.parse_statement(code)
