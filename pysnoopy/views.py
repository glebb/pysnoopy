import json

from .globals import (
    CHARACTER_SCALING,
    DEATH_FALL_GRAVITY_MULTIPLIER,
    MUSIC_SPEED_MULTIPLIER_STEP,
    MUSIC_SPEED_MULTIPLIER_START,
    MOVING_HAZARD_SIZE_SCALE,
    TILE_SCALING,
    PLAYER_GROUND_OFFSET,
    PLAYER_GROUND_OFFSET_STEP,
    PLAYER_MOVEMENT_SPEED,
    PLAYER_START_X,
    GRAVITY,
    PLAYER_JUMP_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHOW_HITBOXES,
    RUN_SPEED_MULTIPLIER_STEP,
)
from .game_state import GameState
from .level_validation import validate_level_file
from .levels import Level3Hook, Level7Hook, LevelHook, LevelSpec, get_default_levels
from .sprites import PlayerCharacter, SkullHazard, TriangleHazard

import random
import types
from typing import cast

import arcade


class GameView(arcade.View):
    def __init__(self, start_level: int = 1, game_state: GameState | None = None):
        super().__init__()
        self.game_state = game_state if game_state is not None else GameState()
        self.background_texture = arcade.load_texture("../assets/images/doghouse.png")

        self.jump_sound = arcade.load_sound("../assets/sound/jump.wav", streaming=False)
        self.fall_sound = arcade.load_sound("../assets/sound/fall.wav", streaming=False)
        self.step_sound = arcade.load_sound(
            "../assets/sound/steps.wav", streaming=False
        )
        self.fall_sound_player = None
        self.step_sound_player = None

        self.physics_engine: arcade.PhysicsEnginePlatformer | None = None
        self.scene: arcade.Scene | None = None
        self.camera: arcade.Camera2D | None = None
        self.player_ground_offset = PLAYER_GROUND_OFFSET
        self.show_hitboxes = SHOW_HITBOXES
        self.debug_text = arcade.Text(
            "",
            10,
            SCREEN_HEIGHT - 24,
            arcade.color.BLACK,
            12,
            bold=True,
        )

        self.tile_map: arcade.TileMap | None = None
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.jump_committed_change_x = 0
        self.jump_start_grace_remaining = 0.0
        self.run_speed_multiplier = self.game_state.run_speed_multiplier
        self.world_bounds: tuple[float, float, float, float] = (
            0.0,
            float(SCREEN_WIDTH),
            0.0,
            float(SCREEN_HEIGHT),
        )
        self.camera_center_y = float(SCREEN_HEIGHT) / 2
        self.level_exit_zone: tuple[float, float, float, float] | None = None

        self.level_specs: list[LevelSpec] = get_default_levels()
        self.level_index = max(0, min(len(self.level_specs) - 1, start_level - 1))
        self.level_spec = self.level_specs[self.level_index]
        self.level: LevelHook = self.level_spec.create_hook()
        self._validated_level_paths: set[str] = set()
        self.moving_hazards: list[TriangleHazard | SkullHazard] = []

    @property
    def player_sprite(self) -> PlayerCharacter:
        assert self.physics_engine is not None
        return cast(PlayerCharacter, self.physics_engine.player_sprite)

    def setup(self):
        if self.fall_sound_player and self.fall_sound.is_playing(player=self.fall_sound_player):
            self.fall_sound.stop(player=self.fall_sound_player)
        if self.step_sound_player and self.step_sound.is_playing(player=self.step_sound_player):
            self.step_sound.stop(player=self.step_sound_player)
        self.fall_sound_player = None
        self.step_sound_player = None

        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.jump_committed_change_x = 0
        self.jump_start_grace_remaining = 0.0
        self.level_spec = self.level_specs[self.level_index]
        self.level = self.level_spec.create_hook()
        background_path = "../assets/images/doghouse.png"
        if self.level_spec.name == "Level 7":
            background_path = "../assets/images/doghouse_long.png"
        self.background_texture = arcade.load_texture(background_path)
        self.run_speed_multiplier = float(self.game_state.run_speed_multiplier)
        player_sprite = PlayerCharacter(scale=CHARACTER_SCALING)
        player_sprite.center_x = PLAYER_START_X

        self.camera = arcade.Camera2D()
        self.camera_center_y = float(SCREEN_HEIGHT) / 2
        self.camera.position = (float(SCREEN_WIDTH) / 2, self.camera_center_y)
        layer_options = {
            "ground": {
                "use_spatial_hash": False,
            },
            "obstacles": {
                "use_spatial_hash": False,
            },
            "foreground": {
                "use_spatial_hash": False,
            },
        }
        if self.level_spec.map_path not in self._validated_level_paths:
            validation_result = validate_level_file(
                level_name=self.level_spec.name,
                map_path=self.level_spec.map_path,
                spawn_object_name=self.level_spec.spawn_object_name,
                exit_object_name=self.level_spec.exit_object_name,
                moving_hazard_object_name=self.level_spec.moving_hazard_object_name,
                skull_hazard_object_name=self.level_spec.skull_hazard_object_name,
                required_object_names=self.level_spec.required_object_names,
            )
            if not validation_result.is_valid:
                raise RuntimeError("\n".join(validation_result.errors))
            for warning in validation_result.warnings:
                print(f"[level warning] {warning}")
            self._validated_level_paths.add(self.level_spec.map_path)

        self.tile_map = arcade.load_tilemap(
            self.level_spec.map_path, TILE_SCALING, layer_options
        )

        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        if isinstance(self.level, Level7Hook):
            obstacles = self.tile_map.sprite_lists.get("obstacles")
            if obstacles is not None:
                for obstacle in obstacles:
                    obstacle.alpha = 0
        self.world_bounds = (
            0.0,
            float(self.tile_map.width * self.tile_map.tile_width * TILE_SCALING),
            0.0,
            float(self.tile_map.height * self.tile_map.tile_height * TILE_SCALING),
        )

        (
            spawn_point,
            spawn_should_snap_to_ground,
            self.level_exit_zone,
            moving_hazard_specs,
            skull_hazard_specs,
        ) = self._load_level_objects_from_map()
        self.moving_hazards = []
        for hazard_spec in moving_hazard_specs:
            hazard = TriangleHazard(width=hazard_spec[2], height=hazard_spec[3])
            hazard.center_x = hazard_spec[0]
            hazard.center_y = hazard_spec[1]
            hazard.change_x = hazard_spec[4] * self.run_speed_multiplier
            hazard.change_y = hazard_spec[5] * self.run_speed_multiplier
            hazard.set_bounds(self.world_bounds)
            self.moving_hazards.append(hazard)
        for hazard_spec in skull_hazard_specs:
            hazard = SkullHazard(
                width=hazard_spec[2],
                height=hazard_spec[3],
                hit_box_points=hazard_spec[6],
            )
            hazard.center_x = hazard_spec[0]
            hazard.center_y = hazard_spec[1]
            hazard.change_x = hazard_spec[4] * self.run_speed_multiplier
            hazard.change_y = hazard_spec[5] * self.run_speed_multiplier
            hazard.set_bounds(self.world_bounds)
            self.moving_hazards.append(hazard)

        if spawn_point is None:
            self._snap_player_to_ground(player_sprite)
        else:
            player_sprite.center_x, player_sprite.center_y = spawn_point
            if spawn_should_snap_to_ground:
                self._snap_player_to_ground(player_sprite)

        self.level.set_speed_multiplier(self.run_speed_multiplier)
        self.level.init_platforms(self.world_bounds)

        if self.level.moving_platforms is not None:
            self.scene.add_sprite_list_after("Platforms", "obstacles")
            for platform in self.level.moving_platforms:
                self.scene.add_sprite("Platforms", platform)

        self.scene.add_sprite_list_before("Hazards", "foreground")
        for hazard in self.moving_hazards:
            self.scene.add_sprite("Hazards", hazard)

        self.scene.add_sprite_list_before("Player", "foreground")
        self.scene.add_sprite("Player", player_sprite)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite,
            gravity_constant=self._current_gravity(),
            walls=self.scene["ground"],
            platforms=self.level.moving_platforms,
        )
        self.level.setup(self.physics_engine, self.world_bounds)

    def _current_move_speed(self):
        return PLAYER_MOVEMENT_SPEED * self.run_speed_multiplier

    def _current_jump_speed(self):
        return PLAYER_JUMP_SPEED * self.run_speed_multiplier

    def _jump_takeoff_speed(self) -> float:
        return self.level.jump_takeoff_speed(
            self._current_jump_speed(),
            self.player_sprite,
        )

    def _resolve_jump_committed_change_x(self) -> float:
        return self.level.resolve_jump_committed_change_x(
            self.player_sprite.change_x,
            self.player_sprite,
        )

    def _current_gravity(self):
        return GRAVITY * (self.run_speed_multiplier ** 2)

    def _apply_music_speed(self):
        self.game_state.restart_music(speed=self.run_speed_multiplier)

    def _stop_step_sound(self):
        if self.step_sound_player and self.step_sound.is_playing(player=self.step_sound_player):
            self.step_sound.stop(player=self.step_sound_player)

    def _refresh_horizontal_movement(self):
        if self.physics_engine is None:
            return
        if self.player_sprite.dying:
            self.player_sprite.change_x = 0
            self._stop_step_sound()
            return

        if self.player_sprite.jumping:
            self.player_sprite.change_x = self.jump_committed_change_x
            self._stop_step_sound()
            return

        base_change_x = 0.0
        if self.left_pressed == self.right_pressed:
            base_change_x = 0.0
        elif self.left_pressed:
            base_change_x = -self._current_move_speed()
        else:
            base_change_x = self._current_move_speed()

        is_grounded = self.physics_engine.can_jump()
        self.player_sprite.change_x = self.level.resolve_horizontal_change_x(
            base_change_x,
            self.player_sprite,
            is_grounded,
        )

        if self.player_sprite.change_x == 0 or self.player_sprite.jumping:
            self._stop_step_sound()
        elif not self.step_sound_player or not self.step_sound.is_playing(
            player=self.step_sound_player
        ):
            self.step_sound_player = self.step_sound.play(loop=True)

    def _snap_player_to_ground(self, player_sprite: PlayerCharacter):
        assert self.scene is not None
        ground_sprites = self.scene["ground"]

        ground_top = None
        nearest_below_top = None
        max_allowed_top = player_sprite.center_y + (player_sprite.height * 0.5)
        for tile in ground_sprites:
            if tile.left <= player_sprite.center_x <= tile.right:
                if ground_top is None or tile.top > ground_top:
                    ground_top = tile.top
                if tile.top <= max_allowed_top and (
                    nearest_below_top is None or tile.top > nearest_below_top
                ):
                    nearest_below_top = tile.top

        target_top = nearest_below_top if nearest_below_top is not None else ground_top
        if target_top is not None:
            min_hit_box_y = min(point[1] for point in player_sprite.hit_box.points)
            player_sprite.center_y = target_top - min_hit_box_y + self.player_ground_offset

    def _adjust_ground_offset(self, delta: int):
        self.player_ground_offset += delta
        if self.physics_engine is not None and self.physics_engine.can_jump():
            self._snap_player_to_ground(self.player_sprite)
        print(f"PLAYER_GROUND_OFFSET={self.player_ground_offset}")

    def _read_object_property(self, obj: dict, property_name: str, default: float) -> float:
        properties = obj.get("properties", [])
        if not isinstance(properties, list):
            return default
        for item in properties:
            if not isinstance(item, dict):
                continue
            if item.get("name") != property_name:
                continue
            try:
                return float(item.get("value", default))
            except (TypeError, ValueError):
                return default
        return default

    def _load_level_objects_from_map(
        self,
    ) -> tuple[
        tuple[float, float] | None,
        bool,
        tuple[float, float, float, float] | None,
        list[tuple[float, float, float, float, float, float]],
        list[
            tuple[
                float,
                float,
                float,
                float,
                float,
                float,
                list[tuple[float, float]] | None,
            ]
        ],
    ]:
        try:
            with open(self.level_spec.map_path, "r", encoding="utf-8") as file_handle:
                raw_map = json.load(file_handle)
        except (FileNotFoundError, json.JSONDecodeError):
            return None, False, None, [], []

        map_height = (
            float(raw_map.get("height", 0))
            * float(raw_map.get("tileheight", 0))
            * TILE_SCALING
        )
        hazard_size_scale = MOVING_HAZARD_SIZE_SCALE
        layers = raw_map.get("layers", [])

        spawn_point: tuple[float, float] | None = None
        spawn_should_snap_to_ground = False
        exit_zone: tuple[float, float, float, float] | None = None
        moving_hazard_specs: list[tuple[float, float, float, float, float, float]] = []
        skull_hazard_specs: list[
            tuple[
                float,
                float,
                float,
                float,
                float,
                float,
                list[tuple[float, float]] | None,
            ]
        ] = []

        for layer in layers:
            if not isinstance(layer, dict) or layer.get("type") != "objectgroup":
                continue

            for obj in layer.get("objects", []):
                if not isinstance(obj, dict):
                    continue
                object_name = obj.get("name")
                x = float(obj.get("x", 0.0)) * TILE_SCALING
                y = float(obj.get("y", 0.0)) * TILE_SCALING

                if object_name == self.level_spec.spawn_object_name:
                    spawn_point = (x, map_height - y)
                    spawn_should_snap_to_ground = bool(obj.get("point", False))
                    continue

                if object_name == self.level_spec.exit_object_name:
                    width = float(obj.get("width", 0.0)) * TILE_SCALING
                    height = float(obj.get("height", 0.0)) * TILE_SCALING
                    if width <= 0 or height <= 0:
                        continue
                    exit_zone = (
                        x + width / 2,
                        map_height - y - height / 2,
                        width,
                        height,
                    )

                if object_name == self.level_spec.moving_hazard_object_name:
                    if "polygon" in obj:
                        # Calculate bounding box for polygon
                        points = obj["polygon"]
                        min_x = min(p.get("x", 0) for p in points)
                        max_x = max(p.get("x", 0) for p in points)
                        min_y = min(p.get("y", 0) for p in points)
                        max_y = max(p.get("y", 0) for p in points)
                        width = max(1.0, float(max_x - min_x) * TILE_SCALING * hazard_size_scale)
                        height = max(1.0, float(max_y - min_y) * TILE_SCALING * hazard_size_scale)
                        # Adjust x, y to be the center of the bounding box
                        x += float(min_x + (max_x - min_x) / 2) * TILE_SCALING
                        y += float(min_y + (max_y - min_y) / 2) * TILE_SCALING
                    else:
                        width = max(
                            1.0,
                            float(obj.get("width", 50.0)) * TILE_SCALING * hazard_size_scale,
                        )
                        height = max(
                            1.0,
                            float(obj.get("height", 50.0)) * TILE_SCALING * hazard_size_scale,
                        )
                    speed_x = self._read_object_property(obj, "speed_x", -2.0)
                    speed_y = self._read_object_property(obj, "speed_y", 0.0)
                    moving_hazard_specs.append(
                        (
                            x,
                            map_height - y - 5.0,  # Lower the hazard slightly to remove gap
                            width,
                            height,
                            speed_x,
                            speed_y,
                        )
                    )

                if object_name == self.level_spec.skull_hazard_object_name:
                    width = max(1.0, float(obj.get("width", 18.0)) * TILE_SCALING)
                    height = max(1.0, float(obj.get("height", 18.0)) * TILE_SCALING)
                    center_x = x + width / 2
                    center_y_tiled = y + height / 2
                    hit_box_points: list[tuple[float, float]] | None = None

                    polygon = obj.get("polygon")
                    if isinstance(polygon, list) and polygon:
                        polygon_pairs: list[tuple[float, float]] = []
                        min_x = float("inf")
                        min_y = float("inf")
                        max_x = float("-inf")
                        max_y = float("-inf")
                        for point in polygon:
                            if not isinstance(point, dict):
                                continue
                            point_x = float(point.get("x", 0.0)) * TILE_SCALING
                            point_y = float(point.get("y", 0.0)) * TILE_SCALING
                            polygon_pairs.append((point_x, point_y))
                            min_x = min(min_x, point_x)
                            min_y = min(min_y, point_y)
                            max_x = max(max_x, point_x)
                            max_y = max(max_y, point_y)
                        if polygon_pairs and min_x != float("inf") and min_y != float("inf"):
                            width = max(1.0, max_x - min_x)
                            height = max(1.0, max_y - min_y)
                            center_x = x + (min_x + max_x) / 2
                            center_y_tiled = y + (min_y + max_y) / 2
                            hit_box_points = []
                            for point_x, point_y in polygon_pairs:
                                hit_box_points.append(
                                    (
                                        point_x - (center_x - x),
                                        -1.0 * (point_y - (center_y_tiled - y)),
                                    )
                                )

                    speed_x = self._read_object_property(obj, "speed_x", 0.0)
                    speed_y = self._read_object_property(obj, "speed_y", 0.0)
                    skull_hazard_specs.append(
                        (
                            center_x,
                            map_height - center_y_tiled,
                            width,
                            height,
                            speed_x,
                            speed_y,
                            hit_box_points,
                        )
                    )

        return (
            spawn_point,
            spawn_should_snap_to_ground,
            exit_zone,
            moving_hazard_specs,
            skull_hazard_specs,
        )

    def _draw_scene_hit_boxes(self):
        assert self.scene is not None
        draw_scene_hit_boxes = getattr(self.scene, "draw_hit_boxes", None)
        if callable(draw_scene_hit_boxes):
            draw_scene_hit_boxes()
            return
        for sprite_list in getattr(self.scene, "sprite_lists", []):
            draw_hit_boxes = getattr(sprite_list, "draw_hit_boxes", None)
            if callable(draw_hit_boxes):
                draw_hit_boxes()

    def _collides_or_touches_obstacles(
        self,
        obstacle_list: arcade.SpriteList,
        touch_margin: float = 1.0,
    ) -> bool:
        if arcade.check_for_collision_with_list(self.player_sprite, obstacle_list):
            return True

        player_left = self.player_sprite.left - touch_margin
        player_right = self.player_sprite.right + touch_margin
        player_bottom = self.player_sprite.bottom - touch_margin
        player_top = self.player_sprite.top + touch_margin

        for obstacle in obstacle_list:
            if player_right < obstacle.left:
                continue
            if player_left > obstacle.right:
                continue
            if player_top < obstacle.bottom:
                continue
            if player_bottom > obstacle.top:
                continue
            return True

        return False

    def _ground_support_metrics(self, vertical_tolerance: float = 8.0) -> tuple[float, float]:
        if self.scene is None:
            return 0.0, 1.0

        ground_sprites = self.scene["ground"]
        hit_box_points = self.player_sprite.hit_box.points
        player_hitbox_left = self.player_sprite.center_x + min(point[0] for point in hit_box_points)
        player_hitbox_right = self.player_sprite.center_x + max(point[0] for point in hit_box_points)
        player_hitbox_width = max(1.0, player_hitbox_right - player_hitbox_left)

        total_overlap_width = 0.0
        for ground_tile in ground_sprites:
            overlap_left = max(player_hitbox_left, ground_tile.left)
            overlap_right = min(player_hitbox_right, ground_tile.right)
            if overlap_right <= overlap_left:
                continue
            is_on_top = (
                self.player_sprite.bottom >= ground_tile.top - vertical_tolerance
                and self.player_sprite.bottom <= ground_tile.top + vertical_tolerance
            )
            if not is_on_top:
                continue
            total_overlap_width += max(0.0, overlap_right - overlap_left)

        return total_overlap_width, player_hitbox_width

    def _can_start_jump(self) -> bool:
        if self.physics_engine is None:
            return False
        if self.physics_engine.can_jump():
            return True

        if not self.level.can_start_jump(self.player_sprite):
            return False

        if self.player_sprite.jumping:
            return False
        return self.jump_start_grace_remaining > 0.0 and self.player_sprite.change_y <= 1.0

    def _enforce_landing_support_margin(self) -> None:
        if self.physics_engine is None:
            return
        if self.player_sprite.dying:
            return

        minimum_overlap_tiles = self.level.min_ground_overlap_tiles()
        if minimum_overlap_tiles is None or minimum_overlap_tiles <= 0.0:
            return
        if not self.physics_engine.can_jump():
            return
        assert self.tile_map is not None

        overlap_width, _ = self._ground_support_metrics()
        required_overlap_width = minimum_overlap_tiles * TILE_SCALING * self.tile_map.tile_width
        if overlap_width < required_overlap_width:
            self._enter_death_state()

    def _is_exit_reached(self) -> bool:
        if self.player_sprite.dying:
            return False

        return self.player_sprite.left >= SCREEN_WIDTH

    def _clamp_player_to_world(self):
        if self.player_sprite.dying:
            return

        left_bound = self.world_bounds[0] - self.player_sprite.width / 2
        soft_zone_width = 48.0
        if (
            self.player_sprite.left < left_bound + soft_zone_width
            and self.player_sprite.change_x < 0
        ):
            distance_to_left = max(0.0, self.player_sprite.left - left_bound)
            damping = max(0.2, min(1.0, distance_to_left / soft_zone_width))
            self.player_sprite.change_x *= damping

        if self.player_sprite.left < left_bound:
            self.player_sprite.left = left_bound
            self.player_sprite.change_x = max(0.0, self.player_sprite.change_x)
            if not self.player_sprite.jumping:
                self._snap_player_to_ground(self.player_sprite)

    def _enforce_full_level3_platform_support(self):
        if self.player_sprite.dying:
            return
        if not isinstance(self.level, Level3Hook):
            return
        assert self.physics_engine is not None
        platforms = self.level.moving_platforms
        if platforms is None:
            return
        if not self.physics_engine.can_jump():
            return

        hit_box_points = self.player_sprite.hit_box.points
        player_hitbox_left = self.player_sprite.center_x + min(point[0] for point in hit_box_points)
        player_hitbox_right = self.player_sprite.center_x + max(point[0] for point in hit_box_points)
        player_hitbox_width = max(1.0, player_hitbox_right - player_hitbox_left)

        vertical_tolerance = 8.0
        support_candidates: list[arcade.Sprite] = []
        for platform in platforms:
            overlap_left = max(player_hitbox_left, platform.left)
            overlap_right = min(player_hitbox_right, platform.right)
            if overlap_right <= overlap_left:
                continue
            is_on_top = (
                self.player_sprite.bottom >= platform.top - vertical_tolerance
                and self.player_sprite.bottom <= platform.top + vertical_tolerance
            )
            if is_on_top:
                support_candidates.append(platform)

        if not support_candidates:
            return

        max_support_ratio = 0.0
        for platform in support_candidates:
            overlap_left = max(player_hitbox_left, platform.left)
            overlap_right = min(player_hitbox_right, platform.right)
            overlap_width = max(0.0, overlap_right - overlap_left)
            support_ratio = overlap_width / player_hitbox_width
            max_support_ratio = max(max_support_ratio, support_ratio)

        if max_support_ratio > 0.5:
            return

        self._enter_death_state()

    def _advance_level(self):
        if self.level_index >= len(self.level_specs) - 1:
            self.level_index = 0
            self.run_speed_multiplier *= RUN_SPEED_MULTIPLIER_STEP
            self.game_state.run_speed_multiplier = self.run_speed_multiplier
            self.game_state.music_speed_multiplier *= MUSIC_SPEED_MULTIPLIER_STEP
            self.game_state.restart_music(speed=self.game_state.music_speed_multiplier)
        else:
            self.level_index += 1
        self.setup()

    def _enter_death_state(self):
        self.player_sprite.die()
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.jump_committed_change_x = 0
        self._stop_step_sound()
        self.fall_sound_player = arcade.play_sound(self.fall_sound, loop=False)

    def on_draw(self):
        assert self.camera is not None
        assert self.scene is not None
        self.clear()
        if self.level_spec.name == "Level 7":
            self.camera.use()
            texture_width = float(self.background_texture.width)
            texture_height = float(self.background_texture.height)
            world_left, _, world_bottom, _ = self.world_bounds
            viewport_width = float(self.window.width) if self.window is not None else float(SCREEN_WIDTH)
            camera_center_x = float(self.camera.position[0])
            if texture_width > 0 and texture_height > 0:
                scale = viewport_width / texture_width
                draw_width = viewport_width
                draw_height = texture_height * scale
            else:
                draw_width = viewport_width
                draw_height = float(SCREEN_HEIGHT)
            arcade.draw_texture_rect(
                self.background_texture,
                rect=arcade.XYWH(
                    max(world_left + (draw_width / 2), camera_center_x),
                    world_bottom + (draw_height / 2),
                    draw_width,
                    draw_height,
                ),
            )
        else:
            arcade.draw_texture_rect(
                self.background_texture,
                rect=arcade.XYWH(
                    SCREEN_WIDTH / 2,
                    SCREEN_HEIGHT / 2,
                    SCREEN_WIDTH,
                    SCREEN_HEIGHT,
                ),
            )
            self.camera.use()
        self.scene.draw()
        self.level.draw()
        if self.show_hitboxes:
            self._draw_scene_hit_boxes()
            self.level.draw_hit_boxes()
        self.debug_text.text = (
            f"{self.level_spec.name}  OFFSET: {self.player_ground_offset}  HITBOXES: {'ON' if self.show_hitboxes else 'OFF'}  SPEED: x{self.run_speed_multiplier:.2f}"
        )
        self.debug_text.draw()

    def on_update(self, delta_time):
        assert self.physics_engine is not None
        assert self.tile_map is not None

        if not self.player_sprite.dying and not self.player_sprite.jumping:
            self._refresh_horizontal_movement()

        level_updated_pre_physics = False
        if isinstance(self.level, Level7Hook) and not self.player_sprite.dying:
            self.level.update()
            level_updated_pre_physics = True

        if self.player_sprite.dying:
            self.player_sprite.center_y += self.player_sprite.change_y
            self.player_sprite.change_y -= (
                self._current_gravity() * DEATH_FALL_GRAVITY_MULTIPLIER
            )
            self.jump_start_grace_remaining = 0.0
        else:
            self.physics_engine.update()
            if self.physics_engine.can_jump():
                self.jump_start_grace_remaining = self.level.jump_start_grace_seconds()
            elif self.jump_start_grace_remaining > 0.0:
                self.jump_start_grace_remaining = max(
                    0.0,
                    self.jump_start_grace_remaining - delta_time,
                )

        self._clamp_player_to_world()
        self._enforce_full_level3_platform_support()
        self._enforce_landing_support_margin()

        if self.player_sprite.jumping and not self.player_sprite.dying:
            if self.player_sprite.change_y <= 0 and self.physics_engine.can_jump():
                self.player_sprite.jumping = False
                self.jump_committed_change_x = 0
                self._refresh_horizontal_movement()

                # Allow immediate jump if UP is still held
                if self.up_pressed and self._can_start_jump():
                    self._stop_step_sound()
                    self.physics_engine.jump(self._jump_takeoff_speed())
                    self.player_sprite.jumping = True
                    self.jump_start_grace_remaining = 0.0
                    self.jump_committed_change_x = self._resolve_jump_committed_change_x()
                    self.player_sprite.change_x = self.jump_committed_change_x
                    arcade.play_sound(self.jump_sound)

        self.player_sprite.update_animation(delta_time)
        for hazard in self.moving_hazards:
            hazard.update()
        if not level_updated_pre_physics:
            self.level.update()
        self._update_camera_position()

        if self.player_sprite.dying:
            if self.step_sound_player and self.step_sound.is_playing(
                player=self.step_sound_player
            ):
                self.step_sound.stop(player=self.step_sound_player)

        obstacle_list = self.tile_map.sprite_lists.get("obstacles")
        if (
            not self.player_sprite.dying
            and obstacle_list is not None
            and self._collides_or_touches_obstacles(obstacle_list)
        ):
            self._enter_death_state()
        elif not self.player_sprite.dying:
            for hazard in self.moving_hazards:
                if self.player_sprite.collides_with_sprite(hazard):
                    self._enter_death_state()
                    break

        death_sprite_top = self.player_sprite.center_y + (self.player_sprite.height / 2)
        if self.player_sprite.dying and death_sprite_top < 0:
            self.setup()
        elif not self.player_sprite.dying and self.player_sprite.center_y < 200:
            self.setup()

        if self._is_exit_reached():
            self._advance_level()

    def _update_camera_position(self):
        assert self.camera is not None

        camera_target_y = self.level.camera_follow_target_y()
        if camera_target_y is not None:
            self.camera_center_y = max(self.camera_center_y, camera_target_y)

        self.camera.position = (float(SCREEN_WIDTH) / 2, self.camera_center_y)

    def on_key_press(self, symbol, modifiers):
        assert self.physics_engine is not None
        minus_keys = {arcade.key.MINUS, getattr(arcade.key, "NUM_SUBTRACT", None)}
        plus_keys = {
            arcade.key.EQUAL,
            getattr(arcade.key, "PLUS", None),
            getattr(arcade.key, "NUM_ADD", None),
        }
        if symbol in minus_keys:
            self._adjust_ground_offset(-PLAYER_GROUND_OFFSET_STEP)
            return
        if symbol in plus_keys:
            self._adjust_ground_offset(PLAYER_GROUND_OFFSET_STEP)
            return
        if symbol == arcade.key.H:
            self.show_hitboxes = not self.show_hitboxes
            print(f"SHOW_HITBOXES={self.show_hitboxes}")
            return

        if self.player_sprite.dying:
            return
        if symbol == arcade.key.UP or symbol == arcade.key.W:
            self.up_pressed = True
            if self._can_start_jump():
                self._stop_step_sound()
                self.physics_engine.jump(self._jump_takeoff_speed())
                self.player_sprite.jumping = True
                self.jump_start_grace_remaining = 0.0
                self.jump_committed_change_x = self._resolve_jump_committed_change_x()
                self.player_sprite.change_x = self.jump_committed_change_x
                arcade.play_sound(self.jump_sound)
        elif symbol == arcade.key.LEFT or symbol == arcade.key.A:
            self.left_pressed = True
            self._refresh_horizontal_movement()

        elif symbol == arcade.key.RIGHT or symbol == arcade.key.D:
            self.right_pressed = True
            self._refresh_horizontal_movement()

    def on_key_release(self, symbol, modifiers):
        if self.player_sprite.dying:
            return
        if symbol == arcade.key.UP or symbol == arcade.key.W:
            self.up_pressed = False
        elif symbol == arcade.key.LEFT or symbol == arcade.key.A:
            self.left_pressed = False
            self._refresh_horizontal_movement()
        elif symbol == arcade.key.RIGHT or symbol == arcade.key.D:
            self.right_pressed = False
            self._refresh_horizontal_movement()

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        pass


class TitleView(arcade.View):
    def __init__(self, game_state: GameState | None = None):
        super().__init__()
        self.game_state = game_state if game_state is not None else GameState()
        self.background_texture = arcade.load_texture("../assets/images/doghouse.png")

        self.letters: arcade.SpriteList | None = None
        self.snoopy_sprite: PlayerCharacter | None = None
        self.snoopy_sprites: arcade.SpriteList | None = None

    def setup(self):
        self.snoopy_sprite = PlayerCharacter(scale=CHARACTER_SCALING)
        self.snoopy_sprite.center_x = SCREEN_WIDTH * 0.25
        self.snoopy_sprite.center_y = SCREEN_HEIGHT * 0.5
        self.snoopy_sprite.change_x = 1.5
        self.snoopy_sprites = arcade.SpriteList()
        self.snoopy_sprites.append(self.snoopy_sprite)

        self.letters = arcade.SpriteList()
        snoopy = ("p", "y", "S", "N", "O", "O", "p", "y")
        height = None
        for i in range(0, len(snoopy)):
            letter_sprite = arcade.create_text_sprite(
                snoopy[i],
                color=arcade.color.COAL,
                font_size=80 * TILE_SCALING,
                font_name="Courier",
                bold=True,
                align="center",
            )
            letter_sprite.center_y = SCREEN_HEIGHT - random.randrange(0, 16)
            width = letter_sprite.width
            if not height:
                height = letter_sprite.height
            letter_sprite.height = height
            if i < 4:
                letter_sprite.center_x = SCREEN_WIDTH / 2 - (4 - i) * width + width / 2
            if i >= 4:
                letter_sprite.center_x = SCREEN_WIDTH / 2 + (i - 4) * width + width / 2
            letter_sprite.change_y = -2

            def update(self, delta_time=0):
                if int(self.center_y) > SCREEN_HEIGHT * 0.85:
                    self.change_y = random.randrange(5, 10) / -10
                if int(self.center_y) <= SCREEN_HEIGHT * 0.7:
                    self.change_y = random.randrange(5, 10) / 10
                self.center_y += self.change_y
                if random.randint(1, 100) == 5:
                    self.color = random.choice(
                        (
                            arcade.color.COAL,
                            arcade.color.CONGO_PINK,
                            arcade.color.SEA_GREEN,
                        )
                    )

            letter_sprite.update = types.MethodType(update, letter_sprite)
            self.letters.append(letter_sprite)

    def on_draw(self):
        assert self.letters is not None
        assert self.snoopy_sprites is not None
        self.clear()
        arcade.draw_texture_rect(
            self.background_texture,
            rect=arcade.XYWH(
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
        )
        self.letters.draw()
        self.snoopy_sprites.draw()

    def on_update(self, delta_time):
        assert self.letters is not None
        assert self.snoopy_sprite is not None
        self.letters.update()

        if self.snoopy_sprite.center_x > SCREEN_WIDTH * 0.8:
            self.snoopy_sprite.change_x = -1.3
        if self.snoopy_sprite.center_x < SCREEN_WIDTH * 0.2:
            self.snoopy_sprite.change_x = 1.3

        self.snoopy_sprite.update_animation(delta_time)
        self.snoopy_sprite.center_x += self.snoopy_sprite.change_x

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.SPACE:
            start_level = int(self.game_state.start_level)
            level1 = GameView(start_level=start_level, game_state=self.game_state)
            level1.run_speed_multiplier = 1.0
            self.game_state.run_speed_multiplier = 1.0
            self.game_state.music_speed_multiplier = MUSIC_SPEED_MULTIPLIER_START
            self.game_state.restart_music(speed=MUSIC_SPEED_MULTIPLIER_START)
            level1.setup()
            self.window.show_view(level1)

    def on_key_release(self, symbol, modifiers):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        pass
