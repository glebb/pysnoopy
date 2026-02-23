from dataclasses import dataclass
from typing import Callable

import arcade

from .globals import SPRITE_PIXEL_SIZE, TILE_SCALING

class LevelHook:
    def __init__(self):
        self.physics_engine: arcade.PhysicsEnginePlatformer | None = None
        self.speed_multiplier = 1.0
        self.level_bounds: tuple[float, float, float, float] | None = None
        self.moving_platforms: arcade.SpriteList | None = None

    def update(self):
        pass

    def draw(self):
        pass

    def draw_hit_boxes(self):
        pass

    def init_platforms(self, world_bounds: tuple[float, float, float, float]) -> None:
        pass

    def setup(
        self,
        physics_engine: arcade.PhysicsEnginePlatformer,
        level_bounds: tuple[float, float, float, float] | None = None,
    ):
        self.physics_engine = physics_engine
        self.level_bounds = level_bounds

    def set_speed_multiplier(self, multiplier: float):
        self.speed_multiplier = multiplier


@dataclass(frozen=True)
class LevelSpec:
    name: str
    map_path: str
    spawn_object_name: str = "spawn"
    exit_object_name: str = "exit"
    moving_hazard_object_name: str = "moving_hazard"
    required_object_names: tuple[str, ...] = ()
    hook_factory: Callable[[], LevelHook] | None = None

    def create_hook(self) -> LevelHook:
        if self.hook_factory is None:
            return LevelHook()
        return self.hook_factory()


class Level3Hook(LevelHook):
    """Moving wood plank that loops left-to-right over the water pit.

    A single logical position is tracked and wrapped within the water span.
    Two sprites are sized and positioned to show only the portion that falls
    inside [water_left_x, water_right_x], so neither sprite ever touches the
    grass or pillars — visually or physically.
    """
    _TILE_PX: int = SPRITE_PIXEL_SIZE * TILE_SCALING    # scaled tile size in px
    _WATER_LEFT_X: float = 9 * _TILE_PX                 # first water column left edge
    _WATER_RIGHT_X: float = 23 * _TILE_PX               # last water column left edge
    _PLATE_WIDTH_TILES: int = 7                         # plate width in tiles
    _PLATE_SPEED: float = 1.6                           # px/frame base speed
    _PLATE_CENTER_Y: float = (20 - 15 - 0.5) * _TILE_PX # surface of ground row 14
    _OFF_SCREEN: float = -10000.0                       # hide sprite outside world

    def _water_width(self) -> float:
        return self._WATER_RIGHT_X - self._WATER_LEFT_X

    def _plate_width(self) -> float:
        return self._PLATE_WIDTH_TILES * self._TILE_PX

    def _start_logical_left(self) -> float:
        """Logical left so only 1 tile column is visible at the water's left edge."""
        return self._WATER_LEFT_X - self._plate_width() + self._TILE_PX

    def init_platforms(self, world_bounds: tuple[float, float, float, float]) -> None:
        self._logical_left: float = self._start_logical_left()
        self.moving_platforms = arcade.SpriteList()
        for _ in range(2):
            plate = arcade.SpriteSolidColor(
                width=int(self._plate_width()),
                height=self._TILE_PX,
                color=(139, 90, 43, 255),
            )
            plate.center_y = self._PLATE_CENTER_Y
            plate.change_x = 0.0  # we position manually; engine must not move them
            self.moving_platforms.append(plate)
        self._apply_positions()

    def _apply_positions(self) -> None:
        """Clip each logical plate segment to the water window and resize to fit."""
        if self.moving_platforms is None:
            return
        water_width = self._water_width()
        plate_width = self._plate_width()
        # Primary starts at _logical_left; echo is one water_width behind.
        logical_lefts = (self._logical_left, self._logical_left - water_width)
        for sprite, log_left in zip(self.moving_platforms, logical_lefts):
            vis_left = max(log_left, self._WATER_LEFT_X)
            vis_right = min(log_left + plate_width, self._WATER_RIGHT_X)
            if vis_right <= vis_left:
                # Not visible in the water window — park off-screen.
                sprite.width = 1
                sprite.center_x = self._OFF_SCREEN
            else:
                sprite.width = vis_right - vis_left
                sprite.center_x = (vis_left + vis_right) / 2.0

    def update(self) -> None:
        if self.moving_platforms is None:
            return
        self._logical_left += self._PLATE_SPEED * self.speed_multiplier
        # Wrap when primary has fully exited right. At this exact moment sprite 2
        # (echo) is showing the plate at water_left — identical to where sprite 1
        # will be after reset — so there is no visual discontinuity.
        if self._logical_left >= self._WATER_RIGHT_X:
            self._logical_left = self._WATER_LEFT_X
        self._apply_positions()


def get_default_levels() -> list[LevelSpec]:
    return [
        LevelSpec(name="Level 1", map_path="../assets/level1.json"),
        LevelSpec(
            name="Level 2",
            map_path="../assets/level2.json",
            required_object_names=("moving_hazard",),
        ),
        LevelSpec(name="Level 3", map_path="../assets/level3.json", hook_factory=Level3Hook),
        LevelSpec(
            name="Level 4",
            map_path="../assets/level4.json",
            required_object_names=("moving_hazard",),
        ),
    ]
