# TODO

Active improvement backlog. When an item is completed, remove it from this file in the same change.

1. Tighten dependency management.
   - Add version ranges instead of bare dependency names.
   - Keep runtime, GUI, SVG, and dev dependencies separated.
   - Consider a lock file only if this is treated as an app rather than a library.

2. Replace assertion-based validation in parser/specmap.
   - Replace production `assert` usage with explicit conversion errors or logged failures.
   - Add tests for malformed blockmaps and missing/unknown inputs.

3. Reduce global mutable configuration risk.
   - Introduce a `Config` dataclass or immutable config object passed into conversion.
   - Keep module globals as a compatibility layer during transition.
   - Add regression tests for repeated conversions with different options in one process.

4. Improve generated-code safety and robustness.
   - Prefer `repr()` or AST-based literal generation where practical.
   - Add fuzz/property tests for names, broadcasts, variables, list values, procedure names, braces, quotes, newlines, keywords, dunder names, and Unicode edge cases.

5. Expand compatibility tests beyond `minimal.sb3`.
   - Add fixture projects for motion, looks, sound, variables/lists, clones, broadcasts, custom blocks, monitors, pen, and SVG assets.
   - Snapshot generated `project.py` for stable fixtures.
   - Add deterministic runtime smoke tests under dummy SDL drivers.

6. Fix Pygame deprecation warning.
   - Replace `set_timing_treshold` with `set_timing_threshold`, with fallback if older Pygame support is needed.
   - Make CI runs warning-clean when practical.

7. Revisit rendering performance.
   - Decide whether rendering should be full-frame or dirty-rect based.
   - If full-frame, simplify around `flip()`.
   - If dirty-rect, avoid unconditional full-screen invalidation and benchmark sprite-heavy projects.
