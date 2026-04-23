import unittest
from unittest import mock

from sb3topy import config, project as project_helpers
from sb3topy.parser import parser as project_parser
from sb3topy.parser import naming
from sb3topy.parser import typing as parser_typing
from sb3topy.parser.specmap import blockmap, mutations
from sb3topy.unpacker import extract


class ParserValidationTests(unittest.TestCase):
    def test_blockmap_requires_code_or_switch(self):
        with self.assertRaisesRegex(ValueError, "must have either code or a switch"):
            blockmap.BlockMap.from_dict(
                "bad_block",
                {
                    "type": "stack",
                    "args": {},
                },
            )

    def test_hat_blockmap_requires_basename(self):
        with self.assertRaisesRegex(ValueError, "missing basename"):
            blockmap.BlockMap.from_dict(
                "bad_hat",
                {
                    "type": "hat",
                    "args": {},
                    "code": "",
                },
            )

    def test_format_code_rejects_missing_arg(self):
        mapped = blockmap.BlockMap(
            "stack",
            {"VALUE": "str"},
            "print({VALUE})",
            {},
        )

        with self.assertRaisesRegex(KeyError, "VALUE"):
            mapped.format_code({})

    def test_format_code_rejects_non_string_arg(self):
        mapped = blockmap.BlockMap(
            "stack",
            {"VALUE": "str"},
            "print({VALUE})",
            {},
        )

        with self.assertRaisesRegex(TypeError, "expected str"):
            mapped.format_code({"VALUE": 123})

    def test_mutation_decorator_rejects_duplicate_opcode(self):
        def replacement(block, target, base):
            return base

        with self.assertRaisesRegex(ValueError, "Duplicate mutation"):
            mutations.mutation("data_variable")(replacement)

    def test_mutation_decorator_rejects_wrong_arity(self):
        def bad_mutation(block, target):
            return block, target

        with self.assertRaisesRegex(ValueError, "must have 3 arguments"):
            mutations.mutation("__test_bad_arity__")(bad_mutation)

    def test_existing_hat_missing_identifier_logs_and_creates_identifier(self):
        old_events = naming.Events.events
        naming.Events.events = None
        try:
            events = naming.Events()
            with self.assertLogs("sb3topy.parser.naming", level="WARNING"):
                identifier = events.existing_hat("broadcast_{BROADCAST}", {
                    "BROADCAST": "message",
                })

            self.assertEqual(identifier, "broadcast_message")
            self.assertEqual(
                events.identifiers.dict["broadcast_message"],
                ["broadcast_message"],
            )
        finally:
            naming.Events.events = old_events

    def test_typing_node_rejects_invalid_type_marker(self):
        node = parser_typing.Node(("target", "var", "name"), set())

        with self.assertRaisesRegex(TypeError, "str or Node"):
            node.add_type(object())

    def test_parser_uses_snapshot_for_var_type_resolution(self):
        config.restore_defaults()
        config.VAR_TYPES = False
        parser_config = config.snapshot_config()
        config.VAR_TYPES = True

        manifest = project_helpers.Manifest()
        sb3 = extract.extract_project(manifest, "tests/minimal.sb3", parser_config)
        self.assertIsNotNone(sb3)

        with mock.patch("sb3topy.parser.targets.DiGraph.resolve") as resolve:
            project_parser.parse_project(sb3, manifest, parser_config)

        resolve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
