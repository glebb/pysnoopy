from globals import (
    TILE_SCALING,
    PLAYER_MOVEMENT_SPEED,
    GRAVITY,
    PLAYER_JUMP_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

import random
import types

import arcade

from sprites import PlayerCharacter, Item


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

        self.jump_sound = arcade.load_sound("../assets/sound/jump.wav", streaming=False)
        self.fall_sound = arcade.load_sound("../assets/sound/fall.wav", streaming=False)
        self.step_sound = arcade.load_sound(
            "../assets/sound/steps.wav", streaming=False
        )
        self.fall_sound_player = None
        self.step_sound_player = None

        self.physics_engine = None
        self.scene = None
        self.camera = None

        self.tile_map = None

        self.levels = (
            {"name": "Level 1", "file": "../assets/level1.json"},
            {"name": "Level 2", "file": "../assets/level2.json"},
        )
        self.level = self.levels[0]

        self.item = Item()
        self.item.center_x = 200
        self.item.center_y = 300
        self.item.change_x = 2
        self.item.change_y = 3

    def setup(self):
        player_sprite = PlayerCharacter()
        player_sprite.center_x = 0
        
        self.camera = arcade.Camera(self.width, self.height)
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
        
        self.tile_map = arcade.load_tilemap(
            self.level["file"], TILE_SCALING, layer_options
        )
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.scene.add_sprite_list_before("Player", "foreground")
        self.scene.add_sprite_list_before("Player", "ground")
        self.scene.add_sprite("Player", player_sprite)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite, gravity_constant=GRAVITY, walls=self.scene["ground"]
        )

    def on_draw(self):
        arcade.start_render()
        self.scene.draw()
        self.item.draw()
        self.camera.use()

    def on_update(self, delta_time):
        self.physics_engine.update()
        self.physics_engine.player_sprite.update_animation(delta_time)
        self.item.update()

        if self.physics_engine.player_sprite.jumping:
            if self.physics_engine.can_jump():
                self.physics_engine.player_sprite.jumping = False
                if self.physics_engine.player_sprite.should_stop:
                    self.physics_engine.player_sprite.change_x = 0

        if self.physics_engine.player_sprite.dying:
            if self.step_sound_player and self.step_sound.is_playing(
                player=self.step_sound_player
            ):
                self.step_sound.stop(player=self.step_sound_player)
            if not self.fall_sound_player or not self.fall_sound.is_playing(
                player=self.fall_sound_player
            ):
                self.fall_sound_player = arcade.play_sound(
                    self.fall_sound, looping=False
                )

        if arcade.check_for_collision_with_list(
            self.physics_engine.player_sprite, self.tile_map.sprite_lists["obstacles"]
        ):
            self.physics_engine.player_sprite.die()

        if self.physics_engine.player_sprite.top < -self.physics_engine.player_sprite.height / 2:
            self.setup()

        if self.physics_engine.player_sprite.left > SCREEN_WIDTH:
            index = self.levels.index(self.level)
            if index >= len(self.levels) - 1:
                index = 0
                global PLAYER_MOVEMENT_SPEED
                global PLAYER_JUMP_SPEED
                global GRAVITY
                PLAYER_MOVEMENT_SPEED = PLAYER_MOVEMENT_SPEED * 1.2
                PLAYER_JUMP_SPEED = PLAYER_JUMP_SPEED * 1.2
                GRAVITY = GRAVITY * 1.45
            else:
                index += 1
            self.level = self.levels[index]
            self.setup()

    def on_key_press(self, key, key_modifiers):
        if self.physics_engine.player_sprite.dying:
            return
        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                if self.step_sound_player and self.step_sound.is_playing(
                    player=self.step_sound_player
                ):
                    self.step_sound.stop(player=self.step_sound_player)
                self.physics_engine.jump(PLAYER_JUMP_SPEED)
                self.physics_engine.player_sprite.jumping = True
                arcade.play_sound(self.jump_sound)
            else:
                return
        elif key == arcade.key.LEFT or key == arcade.key.A:
            if not self.step_sound_player or not self.step_sound.is_playing(
                player=self.step_sound_player
            ):
                self.step_sound_player = self.step_sound.play(loop=True)
            if not self.physics_engine.player_sprite.jumping:
                self.physics_engine.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
            else:
                self.physics_engine.player_sprite.should_stop = False
                return

        elif key == arcade.key.RIGHT or key == arcade.key.D:
            if not self.step_sound_player or not self.step_sound.is_playing(
                player=self.step_sound_player
            ):
                self.step_sound_player = self.step_sound.play(loop=True)
            if not self.physics_engine.player_sprite.jumping:
                self.physics_engine.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
            else:
                self.physics_engine.player_sprite.should_stop = False
                return

    def on_key_release(self, key, key_modifiers):
        if self.physics_engine.player_sprite.dying:
            return
        if key == arcade.key.LEFT or key == arcade.key.A:
            if self.step_sound_player and self.step_sound.is_playing(
                player=self.step_sound_player
            ):
                self.step_sound.stop(player=self.step_sound_player)
            if not self.physics_engine.player_sprite.jumping:
                self.physics_engine.player_sprite.change_x = 0
            else:
                self.physics_engine.player_sprite.should_stop = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            if self.step_sound_player and self.step_sound.is_playing(
                player=self.step_sound_player
            ):
                self.step_sound.stop(player=self.step_sound_player)
            if not self.physics_engine.player_sprite.jumping:
                self.physics_engine.player_sprite.change_x = 0
            else:
                self.physics_engine.player_sprite.should_stop = True

    def on_mouse_motion(self, x, y, delta_x, delta_y):
        pass

    def on_mouse_press(self, x, y, button, key_modifiers):
        pass

    def on_mouse_release(self, x, y, button, key_modifiers):
        pass


class TitleView(arcade.View):
    def __init__(self):
        super().__init__()

        self.letters = None
        self.snoopy_sprite = None

    def setup(self):
        self.snoopy_sprite = PlayerCharacter()
        self.snoopy_sprite.change_x = 1.5

        self.letters = arcade.SpriteList()
        snoopy = ("p", "y", "S", "N", "O", "O", "p", "y")
        height = None
        for i in range(0, len(snoopy)):
            letter_sprite = arcade.create_text_sprite(
                snoopy[i],
                start_x=0,
                start_y=SCREEN_HEIGHT - random.randrange(0, 16),
                color=arcade.color.COAL,
                font_size=80 * TILE_SCALING,
                font_name="Courier",
                bold=True,
                align="center",
            )
            width = letter_sprite.width
            if not height:
                height = letter_sprite.height
            letter_sprite.height = height
            if i < 4:
                letter_sprite.center_x = SCREEN_WIDTH / 2 - (4 - i) * width + width / 2
            if i >= 4:
                letter_sprite.center_x = SCREEN_WIDTH / 2 + (i - 4) * width + width / 2
            letter_sprite.change_y = -2

            def update(self):
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
        arcade.start_render()
        self.letters.draw()
        self.snoopy_sprite.draw()

    def on_update(self, delta_time):
        self.letters.update()

        if self.snoopy_sprite.center_x > SCREEN_WIDTH * 0.8:
            self.snoopy_sprite.change_x = -1.3
        if self.snoopy_sprite.center_x < SCREEN_WIDTH * 0.2:
            self.snoopy_sprite.change_x = 1.3

        self.snoopy_sprite.update_animation(delta_time)
        self.snoopy_sprite.center_x += self.snoopy_sprite.change_x

    def on_key_press(self, key, key_modifiers):
        if key == arcade.key.SPACE:
            level1 = GameView()
            level1.setup()
            self.window.show_view(level1)

    def on_key_release(self, key, key_modifiers):
        pass

    def on_mouse_motion(self, x, y, delta_x, delta_y):
        pass

    def on_mouse_press(self, x, y, button, key_modifiers):
        pass

    def on_mouse_release(self, x, y, button, key_modifiers):
        pass
