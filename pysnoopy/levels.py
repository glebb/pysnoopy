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

    def camera_follow_target_y(self) -> float | None:
        return None

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

    def jump_takeoff_speed(
        self,
        base_speed: float,
        player_sprite: arcade.Sprite,
    ) -> float:
        return base_speed

    def resolve_horizontal_change_x(
        self,
        base_change_x: float,
        player_sprite: arcade.Sprite,
        is_grounded: bool,
    ) -> float:
        return base_change_x

    def resolve_jump_committed_change_x(
        self,
        current_change_x: float,
        player_sprite: arcade.Sprite,
    ) -> float:
        return current_change_x

    def can_start_jump(self, player_sprite: arcade.Sprite) -> bool:
        return True

    def min_ground_overlap_tiles(self) -> float | None:
        return None

    def jump_start_grace_seconds(self) -> float:
        return 0.0


@dataclass(frozen=True)
class LevelSpec:
    name: str
    map_path: str
    spawn_object_name: str = "spawn"
    exit_object_name: str = "exit"
    moving_hazard_object_name: str = "moving_hazard"
    skull_hazard_object_name: str = "skull_hazard"
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

    _TILE_PX: int = SPRITE_PIXEL_SIZE * TILE_SCALING  # scaled tile size in px
    _WATER_LEFT_X: float = 8 * _TILE_PX  # first water column left edge
    _WATER_RIGHT_X: float = 24 * _TILE_PX  # last water column left edge
    _PLATE_WIDTH_TILES: int = 7  # plate width in tiles
    _PLATE_SPEED: float = 1.6  # px/frame base speed
    _PLATE_CENTER_Y: float = (20 - 15 - 0.5) * _TILE_PX  # surface of ground row 14
    _OFF_SCREEN: float = -10000.0  # hide sprite outside world

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


class Level6Hook(LevelHook):
    """Moving red plate that loops right-to-left over the lava pit.

    Uses the same clipped two-sprite approach as Level 3, but mirrored so the
    plate appears from the right side and moves in the opposite direction.
    """

    _TILE_PX: int = SPRITE_PIXEL_SIZE * TILE_SCALING
    _LAVA_LEFT_X: float = 8 * _TILE_PX
    _LAVA_RIGHT_X: float = 24 * _TILE_PX
    _PLATE_WIDTH_TILES: int = 7
    _PLATE_SPEED: float = 1.6
    _PLATE_CENTER_Y: float = (20 - 15 - 0.5) * _TILE_PX
    _OFF_SCREEN: float = -10000.0

    def _lava_width(self) -> float:
        return self._LAVA_RIGHT_X - self._LAVA_LEFT_X

    def _plate_width(self) -> float:
        return self._PLATE_WIDTH_TILES * self._TILE_PX

    def _start_logical_left(self) -> float:
        return self._LAVA_RIGHT_X - self._plate_width()

    def init_platforms(self, world_bounds: tuple[float, float, float, float]) -> None:
        self._logical_left: float = self._start_logical_left()
        self.moving_platforms = arcade.SpriteList()
        for _ in range(2):
            plate = arcade.SpriteSolidColor(
                width=int(self._plate_width()),
                height=self._TILE_PX,
                color=(215, 35, 35, 255),
            )
            plate.center_y = self._PLATE_CENTER_Y
            plate.change_x = 0.0
            self.moving_platforms.append(plate)
        self._apply_positions()

    def _apply_positions(self) -> None:
        if self.moving_platforms is None:
            return
        lava_width = self._lava_width()
        plate_width = self._plate_width()
        logical_lefts = (self._logical_left, self._logical_left + lava_width)
        for sprite, log_left in zip(self.moving_platforms, logical_lefts):
            vis_left = max(log_left, self._LAVA_LEFT_X)
            vis_right = min(log_left + plate_width, self._LAVA_RIGHT_X)
            if vis_right <= vis_left:
                sprite.width = 1
                sprite.center_x = self._OFF_SCREEN
            else:
                sprite.width = vis_right - vis_left
                sprite.center_x = (vis_left + vis_right) / 2.0

    def update(self) -> None:
        if self.moving_platforms is None:
            return
        self._logical_left -= self._PLATE_SPEED * self.speed_multiplier
        if self._logical_left + self._plate_width() <= self._LAVA_LEFT_X:
            self._logical_left = self._LAVA_RIGHT_X - self._plate_width()
        self._apply_positions()


class Level7Hook(LevelHook):
    """Narrow elevator that rises only when the player is exactly centered."""

    _TILE_PX: int = SPRITE_PIXEL_SIZE * TILE_SCALING
    _ELEVATOR_WIDTH_TILES: int = 5
    _ELEVATOR_SPEED: float = 1.2
    _ELEVATOR_CENTER_X: float = 9.5 * _TILE_PX
    _ELEVATOR_START_CENTER_Y: float = (20 - 14 - 0.775) * _TILE_PX
    _ELEVATOR_TARGET_CENTER_Y: float = _ELEVATOR_START_CENTER_Y + (12 * _TILE_PX)
    _CENTER_TOLERANCE_PX: float = 0.5

    def init_platforms(self, world_bounds: tuple[float, float, float, float]) -> None:
        self.moving_platforms = arcade.SpriteList()
        elevator = arcade.SpriteSolidColor(
            width=self._ELEVATOR_WIDTH_TILES * self._TILE_PX,
            height=self._TILE_PX,
            color=(63, 69, 210, 255),
        )
        elevator.center_x = self._ELEVATOR_CENTER_X
        elevator.center_y = self._ELEVATOR_START_CENTER_Y
        elevator.change_x = 0.0
        elevator.change_y = 0.0
        self.moving_platforms.append(elevator)

        self._player_on_elevator = False
        self._camera_target_y: float | None = None

    def _is_player_on_elevator_top(self, player_sprite: arcade.Sprite, elevator: arcade.Sprite) -> bool:
        hit_box_points = player_sprite.hit_box.points
        player_left = player_sprite.center_x + min(point[0] for point in hit_box_points)
        player_right = player_sprite.center_x + max(point[0] for point in hit_box_points)
        player_bottom = player_sprite.center_y + min(point[1] for point in hit_box_points)

        overlap_left = max(player_left, elevator.left)
        overlap_right = min(player_right, elevator.right)
        if overlap_right <= overlap_left:
            return False

        is_on_top = abs(player_bottom - elevator.top) <= 8.0 and player_sprite.change_y <= 1.0
        if not is_on_top:
            return False

        center_offset = abs(player_sprite.center_x - elevator.center_x)
        return center_offset <= self._CENTER_TOLERANCE_PX

    def update(self) -> None:
        if self.moving_platforms is None or self.physics_engine is None:
            return

        elevator = self.moving_platforms[0]
        player_sprite = self.physics_engine.player_sprite
        self._player_on_elevator = self._is_player_on_elevator_top(player_sprite, elevator)

        if self._player_on_elevator and elevator.center_y < self._ELEVATOR_TARGET_CENTER_Y:
            rise_step = min(
                self._ELEVATOR_SPEED * self.speed_multiplier,
                self._ELEVATOR_TARGET_CENTER_Y - elevator.center_y,
            )
            elevator.center_y += rise_step
            elevator.change_y = rise_step
        else:
            elevator.change_y = 0.0

        if elevator.change_y > 0.0:
            self._camera_target_y = player_sprite.center_y
        else:
            self._camera_target_y = None

    def camera_follow_target_y(self) -> float | None:
        return self._camera_target_y


class Level8Hook(LevelHook):
    _TILE_PX: int = SPRITE_PIXEL_SIZE * TILE_SCALING  # World-space size of one tile in pixels.
    _GAP_START_COL: int = 12  # Left tile column where the pit begins.
    _GAP_END_COL: int = 20  # Right tile column where the pit ends.
    _STRIP_WIDTH_TILES: int = 6  # Conveyor strip length (tiles) on both sides of the pit.
    _GROUND_TOP_ROW_FROM_TOP: int = 14  # Ground row index (from top) where strips are drawn/active.
    _STRIP_GLIDE_SPEED: float = 1.8  # Passive rightward glide added while standing on strip.
    _STRIP_FORWARD_BONUS: float = 1.4  # Extra rightward speed when player also holds right on strip.
    _JUMP_CARRY_MAX_RIGHT_SPEED: float = 4.4  # Max rightward horizontal speed carried into jump.
    _TAKEOFF_OVERHANG_TILES: float = 0.25  # How far past edge Snoopy can be and still start jump.
    _MIN_GROUND_OVERLAP_TILES: float = 0.6  # Ground overlap needed to survive/land safely.
    _JUMP_START_GRACE_SECONDS: float = 0.18  # Small late-jump window after leaving ground.

    def _player_hit_box_bounds(self, player_sprite: arcade.Sprite) -> tuple[float, float, float, float]:
        hit_box_points = player_sprite.hit_box.points
        min_x = min(point[0] for point in hit_box_points)
        max_x = max(point[0] for point in hit_box_points)
        min_y = min(point[1] for point in hit_box_points)
        max_y = max(point[1] for point in hit_box_points)
        return (
            player_sprite.center_x + min_x,
            player_sprite.center_x + max_x,
            player_sprite.center_y + min_y,
            player_sprite.center_y + max_y,
        )

    def _overlaps_zone(self, bounds: tuple[float, float, float, float], zone: tuple[float, float, float, float]) -> bool:
        left, right, bottom, top = bounds
        zone_left, zone_right, zone_bottom, zone_top = zone
        return right > zone_left and left < zone_right and top > zone_bottom and bottom < zone_top

    def _boost_zones(self) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
        level_height_tiles = 20
        if self.level_bounds is not None:
            _, _, _, world_top = self.level_bounds
            level_height_tiles = max(1, int(round(world_top / self._TILE_PX)))

        strip_bottom = float((level_height_tiles - (self._GROUND_TOP_ROW_FROM_TOP + 1)) * self._TILE_PX)
        strip_top = strip_bottom + float(self._TILE_PX)

        left_strip = (
            float((self._GAP_START_COL - self._STRIP_WIDTH_TILES) * self._TILE_PX),
            float(self._GAP_START_COL * self._TILE_PX),
            strip_bottom,
            strip_top,
        )
        right_strip = (
            float((self._GAP_END_COL + 1) * self._TILE_PX),
            float((self._GAP_END_COL + 1 + self._STRIP_WIDTH_TILES) * self._TILE_PX),
            strip_bottom,
            strip_top,
        )
        return left_strip, right_strip

    def resolve_horizontal_change_x(
        self,
        base_change_x: float,
        player_sprite: arcade.Sprite,
        is_grounded: bool,
    ) -> float:
        if not is_grounded:
            return base_change_x

        player_bounds = self._player_hit_box_bounds(player_sprite)
        for zone in self._boost_zones():
            if self._overlaps_zone(player_bounds, zone):
                boosted_change_x = base_change_x + self._STRIP_GLIDE_SPEED
                if base_change_x > 0:
                    boosted_change_x += self._STRIP_FORWARD_BONUS
                return boosted_change_x
        return base_change_x

    def resolve_jump_committed_change_x(
        self,
        current_change_x: float,
        player_sprite: arcade.Sprite,
    ) -> float:
        if current_change_x <= 0:
            return current_change_x

        if current_change_x > self._JUMP_CARRY_MAX_RIGHT_SPEED:
            return self._JUMP_CARRY_MAX_RIGHT_SPEED
        return current_change_x

    def min_ground_overlap_tiles(self) -> float | None:
        return self._MIN_GROUND_OVERLAP_TILES

    def can_start_jump(self, player_sprite: arcade.Sprite) -> bool:
        player_left, player_right, _, _ = self._player_hit_box_bounds(player_sprite)
        gap_start_x = float(self._GAP_START_COL * self._TILE_PX)
        gap_end_x = float((self._GAP_END_COL + 1) * self._TILE_PX)

        if player_right <= gap_start_x:
            return True
        if player_left >= gap_end_x:
            return True

        latest_takeoff_left = gap_start_x + (self._TAKEOFF_OVERHANG_TILES * self._TILE_PX)
        return player_left <= latest_takeoff_left

    def jump_start_grace_seconds(self) -> float:
        return self._JUMP_START_GRACE_SECONDS

    def draw(self):
        strip_base_color = (128, 84, 44, 230)
        strip_mark_color = (214, 181, 130, 235)
        strip_height_scale = 2.0 / 3.0

        for zone in self._boost_zones():
            left, right, bottom, top = zone
            conveyor_top = bottom + ((top - bottom) * strip_height_scale)
            strip_width = right - left
            font_size = int(self._TILE_PX * 0.35)
            edge_padding = self._TILE_PX * 0.2
            marks_left = left + edge_padding
            marks_right = right - edge_padding
            marks_width = max(0.0, marks_right - marks_left)
            marks_count = max(3, int(marks_width / (font_size * 1.8)))
            arcade.draw_lrbt_rectangle_filled(
                left,
                right,
                bottom,
                conveyor_top,
                strip_base_color,
            )
            if marks_width <= 0:
                continue
            step = marks_width / marks_count
            for mark_index in range(marks_count):
                mark_x = marks_left + ((mark_index + 0.5) * step)
                arcade.draw_text(
                    ">",
                    mark_x,
                    bottom + ((conveyor_top - bottom) * 0.22),
                    strip_mark_color,
                    font_size=font_size,
                    bold=True,
                    anchor_x="center",
                    anchor_y="baseline",
                )


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
        LevelSpec(
            name="Level 5",
            map_path="../assets/level5.json",
            required_object_names=("skull_hazard",),
        ),
        LevelSpec(name="Level 6", map_path="../assets/level6.json", hook_factory=Level6Hook),
        LevelSpec(name="Level 7", map_path="../assets/level7.json", hook_factory=Level7Hook),
        LevelSpec(name="Level 8", map_path="../assets/level8.json", hook_factory=Level8Hook),
    ]
