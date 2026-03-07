"""Global constants for pySNOOPY.

This module defines game-wide configuration values used by rendering,
physics, controls, and progression. Values here are intended to be treated
as stable defaults for the whole application lifecycle.

Policy: do not place level-specific controls or per-level tuning constants
in this module. Level-specific behavior belongs in level hooks
(`pysnoopy/levels.py`) and level runtime settings (`LevelRuntimeSettings`).
"""

# Window and world scale configuration.
SCREEN_TITLE = "pySNOOPY"

TILE_SCALING = 2

# Screen dimensions in world pixels.
SCREEN_HEIGHT = 360 * TILE_SCALING
SCREEN_WIDTH = int(SCREEN_HEIGHT * (320 / 200))
SPRITE_PIXEL_SIZE = 18

# Sprite and hazard visual scaling.
CHARACTER_SCALING = 1.7
MOVING_HAZARD_SIZE_SCALE = 1

# Player spawn/debug placement and debug toggles.
PLAYER_START_X = SPRITE_PIXEL_SIZE * TILE_SCALING * 2
PLAYER_START_Y = SPRITE_PIXEL_SIZE * TILE_SCALING * 1
PLAYER_GROUND_OFFSET = 0
PLAYER_GROUND_OFFSET_STEP = 0
SHOW_HITBOXES = False

# Character facing direction indices.
RIGHT_FACING = 0
LEFT_FACING = 1

# Core gameplay physics/reality defaults.
PLAYER_MOVEMENT_SPEED = 3.5
GRAVITY = 0.16
PLAYER_JUMP_SPEED = 6.3
DEATH_FALL_GRAVITY_MULTIPLIER = 0.65
LEDGE_MIN_GROUND_OVERLAP_TILES = 2.0
LEDGE_OBSTACLE_FOOT_Y_TOLERANCE = 2.0

# Round progression and music speed defaults.
MUSIC_SPEED_MULTIPLIER_START = 1.0
RUN_SPEED_MULTIPLIER_STEP = 1.7
MUSIC_SPEED_MULTIPLIER_STEP = 1.2
