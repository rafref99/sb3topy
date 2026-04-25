import unittest
from unittest import mock

from sb3topy import config, project as project_helpers
from sb3topy.parser import parser as project_parser
from sb3topy.parser import naming
from sb3topy.parser import typing as parser_typing
from sb3topy.parser.specmap import blockmap, data, mutations
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

    def test_username_reporter_uses_engine_config_namespace(self):
        project_data = {
            "targets": [{
                "isStage": True,
                "name": "Stage",
                "variables": {"user-id": ["user", ""]},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "hat": {
                        "opcode": "event_whenflagclicked",
                        "next": "set",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                    },
                    "set": {
                        "opcode": "data_setvariableto",
                        "next": None,
                        "parent": "hat",
                        "inputs": {"VALUE": [2, "username"]},
                        "fields": {"VARIABLE": ["user", "user-id"]},
                        "shadow": False,
                        "topLevel": False,
                    },
                    "username": {
                        "opcode": "sensing_username",
                        "next": None,
                        "parent": "set",
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": False,
                    },
                },
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 0,
            }],
        }

        code = project_parser.parse_project(
            project_helpers.Project(project_data),
            project_helpers.Manifest(),
            config.snapshot_config(),
        )

        self.assertIn("self.var_user = engine.config.USERNAME", code)
        self.assertNotIn("config.USERNAME", code.replace("engine.config.USERNAME", ""))

    def test_plain_broadcast_does_not_yield_before_next_block(self):
        code = data.BLOCKS["event_broadcast"].format_code({
            "BROADCAST_INPUT": "'update gui'",
        })

        self.assertEqual(code, "util.send_broadcast('update gui')")

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

    def test_nested_operator_parentheses_are_preserved(self):
        project_data = {
            "targets": [{
                "isStage": True,
                "name": "Stage",
                "variables": {"varid": ["x", 0]},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "hat": {
                        "opcode": "event_whenflagclicked",
                        "next": "set",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                    },
                    "set": {
                        "opcode": "data_setvariableto",
                        "next": None,
                        "parent": "hat",
                        "inputs": {"VALUE": [3, "mul", [10, "0"]]},
                        "fields": {"VARIABLE": ["x", "varid"]},
                        "shadow": False,
                        "topLevel": False,
                    },
                    "mul": {
                        "opcode": "operator_multiply",
                        "next": None,
                        "parent": "set",
                        "inputs": {
                            "NUM1": [3, "sub", [4, ""]],
                            "NUM2": [1, [4, "3"]],
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False,
                    },
                    "sub": {
                        "opcode": "operator_subtract",
                        "next": None,
                        "parent": "mul",
                        "inputs": {
                            "NUM1": [1, [4, "10"]],
                            "NUM2": [1, [4, "6"]],
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False,
                    },
                },
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 0,
            }]
        }

        code = project_parser.parse_project(
            project_helpers.Project(project_data),
            project_helpers.Manifest(),
            config.snapshot_config(),
        )

        self.assertIn("self.var_x = ((10 - 6) * 3)", code)

    def test_variable_name_starting_with_var_gets_var_prefix(self):
        project_data = {
            "targets": [{
                "isStage": False,
                "name": "Sprite",
                "variables": {"variant-id": ["variant", "1"]},
                "lists": {},
                "broadcasts": {},
                "blocks": {},
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 0,
            }]
        }

        code = project_parser.parse_project(
            project_helpers.Project(project_data),
            project_helpers.Manifest(),
            config.snapshot_config(),
        )

        self.assertIn("self.var_variant = 1", code)
        self.assertNotIn("self.variant = 1", code)

    def test_monitor_uses_sprite_name_for_local_variable(self):
        project_data = {
            "targets": [{
                "isStage": True,
                "name": "Stage",
                "variables": {},
                "lists": {},
                "broadcasts": {},
                "blocks": {},
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 0,
            }, {
                "isStage": False,
                "name": "Sprite",
                "variables": {"variant-id": ["variant", "1"]},
                "lists": {},
                "broadcasts": {},
                "blocks": {},
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 1,
            }],
            "monitors": [{
                "mode": "default",
                "opcode": "data_variable",
                "params": {"VARIABLE": "variant"},
                "spriteName": "Sprite",
                "x": 5,
                "y": 75,
                "visible": False,
            }],
        }

        code = project_parser.parse_project(
            project_helpers.Project(project_data),
            project_helpers.Manifest(),
            config.snapshot_config(),
        )

        self.assertIn("'variant', SPRITES['Sprite'], 'var_variant'", code)

    def test_sensing_costume_number_switches_to_costume_property(self):
        project_data = {
            "targets": [{
                "isStage": True,
                "name": "Stage",
                "variables": {"x-id": ["x", 0]},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "hat": {
                        "opcode": "event_whenflagclicked",
                        "next": "set",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                    },
                    "set": {
                        "opcode": "data_setvariableto",
                        "next": None,
                        "parent": "hat",
                        "inputs": {"VALUE": [3, "sensing", [10, "0"]]},
                        "fields": {"VARIABLE": ["x", "x-id"]},
                        "shadow": False,
                        "topLevel": False,
                    },
                    "sensing": {
                        "opcode": "sensing_of",
                        "next": None,
                        "parent": "set",
                        "inputs": {"OBJECT": [1, [10, "Sprite"]]},
                        "fields": {"PROPERTY": ["costume #", None]},
                        "shadow": False,
                        "topLevel": False,
                    },
                },
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 0,
            }, {
                "isStage": False,
                "name": "Sprite",
                "variables": {},
                "lists": {},
                "broadcasts": {},
                "blocks": {},
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 1,
            }],
        }

        code = project_parser.parse_project(
            project_helpers.Project(project_data),
            project_helpers.Manifest(),
            config.snapshot_config(),
        )

        self.assertIn("self.var_x = util.sprites['Sprite'].costume.number", code)
        self.assertNotIn("var_costume", code)

    def test_blank_custom_block_argument_is_not_coerced_to_zero(self):
        project_data = {
            "targets": [{
                "isStage": True,
                "name": "Stage",
                "variables": {"x-id": ["x", 0]},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "hat": {
                        "opcode": "event_whenflagclicked",
                        "next": "call_blank",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                    },
                    "call_blank": {
                        "opcode": "procedures_call",
                        "next": "call_number",
                        "parent": "hat",
                        "inputs": {"arg-id": [1, [10, ""]]},
                        "fields": {},
                        "shadow": False,
                        "topLevel": False,
                        "mutation": {
                            "tagName": "mutation",
                            "children": [],
                            "proccode": "upshift %s",
                            "argumentids": "[\"arg-id\"]",
                            "warp": "false",
                        },
                    },
                    "call_number": {
                        "opcode": "procedures_call",
                        "next": None,
                        "parent": "call_blank",
                        "inputs": {"arg-id": [1, [10, "1"]]},
                        "fields": {},
                        "shadow": False,
                        "topLevel": False,
                        "mutation": {
                            "tagName": "mutation",
                            "children": [],
                            "proccode": "upshift %s",
                            "argumentids": "[\"arg-id\"]",
                            "warp": "false",
                        },
                    },
                    "def": {
                        "opcode": "procedures_definition",
                        "next": "set",
                        "parent": None,
                        "inputs": {"custom_block": [1, "proto"]},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                    },
                    "proto": {
                        "opcode": "procedures_prototype",
                        "next": None,
                        "parent": "def",
                        "inputs": {},
                        "fields": {},
                        "shadow": True,
                        "topLevel": False,
                        "mutation": {
                            "tagName": "mutation",
                            "children": [],
                            "proccode": "upshift %s",
                            "argumentids": "[\"arg-id\"]",
                            "argumentnames": "[\"to\"]",
                            "argumentdefaults": "[\"\"]",
                            "warp": "false",
                        },
                    },
                    "set": {
                        "opcode": "data_setvariableto",
                        "next": None,
                        "parent": "def",
                        "inputs": {"VALUE": [3, "arg", [10, ""]]},
                        "fields": {"VARIABLE": ["x", "x-id"]},
                        "shadow": False,
                        "topLevel": False,
                    },
                    "arg": {
                        "opcode": "argument_reporter_string_number",
                        "next": None,
                        "parent": "set",
                        "inputs": {},
                        "fields": {"VALUE": ["to", None]},
                        "shadow": False,
                        "topLevel": False,
                    },
                },
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 0,
            }]
        }

        code = project_parser.parse_project(
            project_helpers.Project(project_data),
            project_helpers.Manifest(),
            config.snapshot_config(),
        )

        self.assertIn("await self.my_upshift(util, '')", code)
        self.assertIn("await self.my_upshift(util, 1)", code)
        self.assertNotIn("await self.my_upshift(util, 0)", code)

    def test_inline_variable_reporter_prefers_id_over_display_name(self):
        project_data = {
            "targets": [{
                "isStage": True,
                "name": "Stage",
                "variables": {"background-id": ["Background", 1]},
                "lists": {},
                "broadcasts": {},
                "blocks": {},
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 0,
            }, {
                "isStage": False,
                "name": "Sprite",
                "variables": {"x-id": ["x", 0]},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "hat": {
                        "opcode": "event_whenflagclicked",
                        "next": "set",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                    },
                    "set": {
                        "opcode": "data_setvariableto",
                        "next": None,
                        "parent": "hat",
                        "inputs": {"VALUE": [3, "letter", [10, ""]]},
                        "fields": {"VARIABLE": ["x", "x-id"]},
                        "shadow": False,
                        "topLevel": False,
                    },
                    "letter": {
                        "opcode": "operator_letter_of",
                        "next": None,
                        "parent": "set",
                        "inputs": {
                            "LETTER": [3, [12, "BACKGROUND", "background-id"], [6, "1"]],
                            "STRING": [1, [10, "abcdefg"]],
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False,
                    },
                },
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 1,
            }],
        }

        code = project_parser.parse_project(
            project_helpers.Project(project_data),
            project_helpers.Manifest(),
            config.snapshot_config(),
        )

        self.assertIn("letter_of('abcdefg', toint(util.sprites.stage.var_Background))", code)
        self.assertNotIn("var_BACKGROUND", code)

    def test_copied_script_dangling_variable_id_falls_back_to_project_name(self):
        project_data = {
            "targets": [{
                "isStage": True,
                "name": "Stage",
                "variables": {},
                "lists": {},
                "broadcasts": {},
                "blocks": {},
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 0,
            }, {
                "isStage": False,
                "name": "Source",
                "variables": {"shared-id": ["roll", 0]},
                "lists": {},
                "broadcasts": {},
                "blocks": {},
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 1,
            }, {
                "isStage": False,
                "name": "Copied",
                "variables": {"x-id": ["x", 0]},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "hat": {
                        "opcode": "event_whenflagclicked",
                        "next": "set",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                    },
                    "set": {
                        "opcode": "data_setvariableto",
                        "next": "change_roll",
                        "parent": "hat",
                        "inputs": {"VALUE": [3, [12, "ROLL", "shared-id"], [10, "0"]]},
                        "fields": {"VARIABLE": ["x", "x-id"]},
                        "shadow": False,
                        "topLevel": False,
                    },
                    "change_roll": {
                        "opcode": "data_changevariableby",
                        "next": None,
                        "parent": "set",
                        "inputs": {"VALUE": [1, [4, "1"]]},
                        "fields": {"VARIABLE": ["ROLL", "shared-id"]},
                        "shadow": False,
                        "topLevel": False,
                    },
                },
                "comments": {},
                "currentCostume": 0,
                "costumes": [],
                "sounds": [],
                "volume": 100,
                "layerOrder": 2,
            }],
        }

        code = project_parser.parse_project(
            project_helpers.Project(project_data),
            project_helpers.Manifest(),
            config.snapshot_config(),
        )

        self.assertIn("self.var_roll = 0", code)
        self.assertIn("self.var_x = self.var_roll", code)
        self.assertIn("self.var_roll += 1", code)
        self.assertNotIn("var_sharedid", code)


if __name__ == "__main__":
    unittest.main()
