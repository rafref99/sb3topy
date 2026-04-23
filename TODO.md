# TODO

Active improvement backlog. When an item is completed, remove it from this file in the same change.

1. Continue reducing global mutable configuration risk.
   - Introduce a `Config` dataclass or immutable config object passed into conversion.
   - Keep module globals as a compatibility layer during transition.

2. Continue improving generated-code safety and robustness.
   - Consider AST-based generation for larger generated-code surfaces where practical.
   - Add fuzz/property tests for names, broadcasts, variables, list values, procedure names, braces, quotes, newlines, keywords, dunder names, and Unicode edge cases.

3. Expand compatibility tests beyond `minimal.sb3`.
   - Add fixture projects for motion, looks, sound, variables/lists, clones, broadcasts, custom blocks, monitors, pen, and SVG assets.
   - Snapshot generated `project.py` for stable fixtures.
   - Add deterministic runtime smoke tests under dummy SDL drivers.
