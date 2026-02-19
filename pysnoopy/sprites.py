import arcade

from .globals import (
    CHARACTER_SCALING,
    LEFT_FACING,
    PLAYER_JUMP_SPEED,
    PLAYER_START_X,
    PLAYER_START_Y,
    RIGHT_FACING,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


class PlayerCharacter(arcade.Sprite):
    def __init__(self):
        super().__init__()

        self.character_face_direction = RIGHT_FACING

        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        self.jumping = False
        self.dying = False

        main_path = "../assets/images/"
        self.idle_texture_pair = load_texture_pair(f"{main_path}snoopy1.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}snoopy_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}snoopy_down.png")

        self.walk_textures = []
        for i in range(3):
            texture = load_texture_pair(f"{main_path}snoopy{i+1}.png")
            self.walk_textures.append(texture)

        self.texture = self.idle_texture_pair[0]
        self.direction_hit_boxes = {
            RIGHT_FACING: self._build_scaled_hit_box(self.idle_texture_pair[RIGHT_FACING]),
            LEFT_FACING: self._build_scaled_hit_box(self.idle_texture_pair[LEFT_FACING]),
        }
        self.hit_box = arcade.hitbox.RotatableHitBox(
            self.direction_hit_boxes[self.character_face_direction]
        )

        self.change_x = 0
        self.update_walk = 0

        # Some defaults to place character
        self.center_x = PLAYER_START_X
        self.center_y = PLAYER_START_Y

    def _set_texture(self, texture):
        if self.texture is texture:
            return
        self.texture = texture
        self._sync_hit_box_with_direction()

    def _build_scaled_hit_box(self, texture) -> list[tuple[float, float]]:
        scale = self.scale
        if isinstance(scale, tuple):
            scale_x = float(scale[0])
            scale_y = float(scale[1])
        else:
            scale_x = float(scale)
            scale_y = float(scale)
        return [
            (point[0] * scale_x, point[1] * scale_y)
            for point in texture.hit_box_points
        ]

    def _sync_hit_box_with_direction(self):
        self.hit_box = arcade.hitbox.RotatableHitBox(
            self.direction_hit_boxes[self.character_face_direction]
        )

    def die(self):
        self.dying = True
        self.hit_box = arcade.hitbox.RotatableHitBox([(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)])
        self.change_x = 0
        self.change_y = min(self.change_y, -PLAYER_JUMP_SPEED)
        
    def update_animation(self, delta_time: float = 1 / 60):
        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        if self.dying:
            self._set_texture(self.fall_texture_pair[self.character_face_direction])
            return

        # Jumping/falling animation while airborne
        if self.jumping:
            if self.change_y >= 0:
                self._set_texture(self.jump_texture_pair[self.character_face_direction])
            else:
                self._set_texture(self.fall_texture_pair[self.character_face_direction])
            return

        # Idle animation
        if self.change_x == 0:
            self._set_texture(self.idle_texture_pair[self.character_face_direction])
            return

        # Walking animation
        if self.update_walk == 5:  # Update frame only every 5 cycles
            self.cur_texture += 1
            if self.cur_texture > 2:
                self.cur_texture = 0
            self._set_texture(
                self.walk_textures[self.cur_texture][self.character_face_direction]
            )
            self.update_walk = 0
        self.update_walk += 1


def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    texture = arcade.load_texture(filename)
    return [
        texture,
        texture.flip_left_right(),
    ]


# Rectangle info
RECT_WIDTH = 50
RECT_HEIGHT = 50
RECT_COLOR = arcade.color.DARK_BROWN


class Item(arcade.Sprite):
    def __init__(self):
        super().__init__()

        # Set up attribute variables

        # Where we are
        self.center_x = 0
        self.center_y = 0

        # Where we are going
        self.change_x = 0
        self.change_y = 0
        self.hit_box = arcade.hitbox.RotatableHitBox(
            [(-20, -20), (-20, 20), (20, 20), (20, -20)]
        )

    def update(self):
        # Move the rectangle
        self.center_x += self.change_x
        self.center_y += self.change_y
        # Check if we need to bounce of right edge
        if self.center_x > SCREEN_WIDTH - RECT_WIDTH / 2:
            self.change_x *= -1
        # Check if we need to bounce of top edge
        if self.center_y > SCREEN_HEIGHT - RECT_HEIGHT / 2:
            self.change_y *= -1
        # Check if we need to bounce of left edge
        if self.center_x < RECT_WIDTH / 2:
            self.change_x *= -1
        # Check if we need to bounce of bottom edge
        if self.center_y < RECT_HEIGHT / 2:
            self.change_y *= -1

    def draw(self):
        # Draw the rectangle
        arcade.draw_lbwh_rectangle_filled(
            self.center_x - RECT_WIDTH / 2,
            self.center_y - RECT_HEIGHT / 2,
            RECT_WIDTH,
            RECT_HEIGHT,
            RECT_COLOR,
        )
