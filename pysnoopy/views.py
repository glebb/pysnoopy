from .globals import (
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
from .levels import Level_1, Level_2, Level_3
from .sprites import PlayerCharacter

import random
import types
from typing import cast

import arcade


class GameView(arcade.View):
    def __init__(self, start_level: int = 1):
        super().__init__()

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
        self.jump_committed_change_x = 0
        self.run_speed_multiplier = 1.0

        self.levels = (Level_1(), Level_2(), Level_3())
        start_index = max(0, min(len(self.levels) - 1, start_level - 1))
        self.level = self.levels[start_index]

    @property
    def player_sprite(self) -> PlayerCharacter:
        assert self.physics_engine is not None
        return cast(PlayerCharacter, self.physics_engine.player_sprite)

    def setup(self):
        self.left_pressed = False
        self.right_pressed = False
        self.jump_committed_change_x = 0
        self.run_speed_multiplier = float(
            getattr(self.window, "run_speed_multiplier", self.run_speed_multiplier)
        )
        player_sprite = PlayerCharacter()
        player_sprite.center_x = PLAYER_START_X

        self.camera = arcade.Camera2D()
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
        self.tile_map = arcade.load_tilemap(self.level.map, TILE_SCALING, layer_options)

        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self._snap_player_to_ground(player_sprite)
        self.scene.add_sprite_list_before("Player", "foreground")
        self.scene.add_sprite("Player", player_sprite)
        
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite,
            gravity_constant=self._current_gravity(),
            walls=self.scene["ground"],
        )
        self.level.set_speed_multiplier(self.run_speed_multiplier)
        self.level.setup(self.physics_engine)

    def _current_move_speed(self):
        return PLAYER_MOVEMENT_SPEED * self.run_speed_multiplier

    def _current_jump_speed(self):
        return PLAYER_JUMP_SPEED * self.run_speed_multiplier

    def _current_gravity(self):
        return GRAVITY * (self.run_speed_multiplier ** 2)

    def _apply_music_speed(self):
        if self.window is None:
            return
        music_sound = getattr(self.window, "music_sound", None)
        music_player = getattr(self.window, "music_player", None)
        if music_sound is None:
            return
        if music_player is not None:
            music_sound.stop(player=music_player)
        setattr(
            self.window,
            "music_player",
            arcade.play_sound(
                music_sound,
                volume=0.5,
                loop=True,
                speed=self.run_speed_multiplier,
            ),
        )

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

        if self.left_pressed == self.right_pressed:
            self.player_sprite.change_x = 0
        elif self.left_pressed:
            self.player_sprite.change_x = -self._current_move_speed()
        else:
            self.player_sprite.change_x = self._current_move_speed()

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
        for tile in ground_sprites:
            if tile.left <= player_sprite.center_x <= tile.right:
                if ground_top is None or tile.top > ground_top:
                    ground_top = tile.top

        if ground_top is not None:
            min_hit_box_y = min(point[1] for point in player_sprite.hit_box.points)
            player_sprite.center_y = ground_top - min_hit_box_y + self.player_ground_offset

    def _adjust_ground_offset(self, delta: int):
        self.player_ground_offset += delta
        if self.physics_engine is not None and self.physics_engine.can_jump():
            self._snap_player_to_ground(self.player_sprite)
        print(f"PLAYER_GROUND_OFFSET={self.player_ground_offset}")

    def on_draw(self):
        assert self.camera is not None
        assert self.scene is not None
        self.clear()
        self.camera.use()
        self.scene.draw()
        self.level.draw()
        if self.show_hitboxes:
            self.scene.draw_hit_boxes()
            self.level.draw_hit_boxes()
        self.debug_text.text = (
            f"OFFSET: {self.player_ground_offset}  HITBOXES: {'ON' if self.show_hitboxes else 'OFF'}  SPEED: x{self.run_speed_multiplier:.2f}"
        )
        self.debug_text.draw()

    def on_update(self, delta_time):
        assert self.physics_engine is not None
        assert self.tile_map is not None

        if self.player_sprite.dying:
            self.player_sprite.center_y += self.player_sprite.change_y
            self.player_sprite.change_y -= self._current_gravity()
        else:
            self.physics_engine.update()

        self.player_sprite.update_animation(delta_time)
        self.level.update()
        
        if self.player_sprite.jumping:
            if self.physics_engine.can_jump():
                self.player_sprite.jumping = False
                self.jump_committed_change_x = 0
                self._refresh_horizontal_movement()

        if self.player_sprite.dying:
            if self.step_sound_player and self.step_sound.is_playing(
                player=self.step_sound_player
            ):
                self.step_sound.stop(player=self.step_sound_player)
            if not self.fall_sound_player or not self.fall_sound.is_playing(
                player=self.fall_sound_player
            ):
                self.fall_sound_player = arcade.play_sound(
                    self.fall_sound, loop=False
                )

        if (
            not self.player_sprite.dying
            and arcade.check_for_collision_with_list(
                self.player_sprite, self.tile_map.sprite_lists["obstacles"]
            )
        ):
            self.player_sprite.die()

        if self.player_sprite.dying and self.player_sprite.top < 0:
            self.setup()
        elif not self.player_sprite.dying and self.player_sprite.center_y < 200:
            self.setup()

        if self.player_sprite.left > SCREEN_WIDTH:
            index = self.levels.index(self.level)
            if index >= len(self.levels) - 1:
                index = 0
                self.run_speed_multiplier *= RUN_SPEED_MULTIPLIER_STEP
                if self.window is not None:
                    setattr(self.window, "run_speed_multiplier", self.run_speed_multiplier)
                self._apply_music_speed()
            else:
                index += 1
            self.level = self.levels[index]
            self.setup()

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
            if self.physics_engine.can_jump():
                self._stop_step_sound()
                self.physics_engine.jump(self._current_jump_speed())
                self.player_sprite.jumping = True
                self.jump_committed_change_x = self.player_sprite.change_x
                arcade.play_sound(self.jump_sound)
            else:
                return
        elif symbol == arcade.key.LEFT or symbol == arcade.key.A:
            self.left_pressed = True
            self._refresh_horizontal_movement()

        elif symbol == arcade.key.RIGHT or symbol == arcade.key.D:
            self.right_pressed = True
            self._refresh_horizontal_movement()

    def on_key_release(self, symbol, modifiers):
        if self.player_sprite.dying:
            return
        if symbol == arcade.key.LEFT or symbol == arcade.key.A:
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
    def __init__(self):
        super().__init__()

        self.letters: arcade.SpriteList | None = None
        self.snoopy_sprite: PlayerCharacter | None = None
        self.snoopy_sprites: arcade.SpriteList | None = None

    def setup(self):
        self.snoopy_sprite = PlayerCharacter()
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
            start_level = int(getattr(self.window, "start_level", 1))
            level1 = GameView(start_level=start_level)
            level1.run_speed_multiplier = 1.0
            if self.window is not None:
                setattr(self.window, "run_speed_multiplier", 1.0)
                music_sound = getattr(self.window, "music_sound", None)
                music_player = getattr(self.window, "music_player", None)
                if music_sound is not None and music_player is not None:
                    music_sound.stop(player=music_player)
                    setattr(
                        self.window,
                        "music_player",
                        arcade.play_sound(
                        music_sound, volume=0.5, loop=True, speed=1.0
                        ),
                    )
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
