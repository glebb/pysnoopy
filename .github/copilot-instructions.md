# Project Guidelines

## Code Style
- Keep modern typed Python style used in this repo: built-in generics and `| None` unions.
- Use runtime guards with `assert ... is not None` before using view state (camera, scene, physics engine).
- Follow lint limits from `.flake8`: max line length 120 and max complexity 10.
- Preserve existing naming around map layers/objects: `ground`, `obstacles`, `foreground`, `spawn`, `exit`, `moving_hazard`.

## Architecture
- Entry point is `pysnoopy/main.py`: it creates the Arcade window, initializes `GameState`, and shows `TitleView` or `GameView`.
- Gameplay is view-based in `pysnoopy/views.py`: `TitleView` starts the run, `GameView` owns tilemap/scene/camera/physics and progression.
- Level catalog is centralized in `pysnoopy/levels.py` via `LevelSpec` and optional `LevelHook` implementations.
- Level schema and map checks are centralized in `pysnoopy/level_validation.py`.

## Build and Test
- Setup environment and dependencies:
  - `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run game:
  - `python -m pysnoopy.main`
  - `python -m pysnoopy.main --start-level 3`
- Validate level files:
  - `python -m pysnoopy.validate_levels`
  - `python -m pysnoopy.validate_levels --strict`

## Project Conventions
- Required Tiled tile layers are `ground`, `obstacles`, and `foreground`.
- `spawn` and `exit` objects are optional but should exist; missing objects currently trigger warnings and fallback behavior.
- `moving_hazard` objects can be rectangles (must have positive size) or polygons. Optional `speed_x` and `speed_y` properties must be numeric.
- Level progression currently advances when player reaches the right side and wraps to level 1 after the last level, increasing speed multiplier.
- Level-specific requirements belong in `LevelSpec.required_object_names` (for example, level 2 requires `moving_hazard`).

## Level Reference Workflow (Self Instructions)
- Before changing any level map, check original C64 references first, then design.
- Primary source: C64-Wiki Snoopy page (`https://www.c64-wiki.com/wiki/Snoopy`) and its per-level GIFs (`SnoopyLevel01.gif` ... `SnoopyLevel02.gif`).
- Secondary source: longplay footage listed on C64-Wiki (Archive.org, YouTube, C64-longplays). Use it to verify movement rhythm and hazard timing.
- If a source is blocked (for example login-gated pages), use available mirrors from C64-Wiki links and continue with the best accessible evidence.
- Recreate in this order: 1) floor/pit silhouette, 2) traversal/bridge structure, 3) hazard count + approximate speed lanes, 4) foreground/decorative details.
- Keep gameplay logic unchanged unless explicitly requested: right-edge completion remains the progression rule.
- After edits, always run `python -m pysnoopy.validate_levels`; if needed, run `--strict` and report any pre-existing warnings separately from new issues.

## Integration Points
- Core external dependency is Arcade (`arcade==3.3.3`) for rendering, physics, and audio.
- Tiled maps are loaded through `arcade.load_tilemap(...)`; object layers are parsed from JSON in `GameView`.
- Hazards are drawn using `arcade.Scene` sprite lists to manage draw order (e.g., behind foreground fences but in front of the player).
- Asset loading assumes current working directory is set by startup code in `pysnoopy/main.py`.

## Security
- No auth, network, or secret management exists in this codebase.
- Primary trust boundary is local level JSON input; keep validation (`validate_level_file`) in place when adding/changing maps.
