import arcade

from globals import (
    CHARACTER_SCALING,
    LEFT_FACING,
    RIGHT_FACING,
    SCREEN_WIDTH,
    TILE_SCALING,
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
        self.should_stop = False

        main_path = "../assets/images/"
        self.idle_texture_pair = load_texture_pair(f"{main_path}snoopy1.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}snoopy_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}snoopy_down.png")

        self.walk_textures = []
        for i in range(3):
            texture = load_texture_pair(f"{main_path}snoopy{i+1}.png")
            self.walk_textures.append(texture)

        self.texture = self.idle_texture_pair[0]

        self.hit_box = self.texture.hit_box_points

        self.change_x = 0
        self.update_walk = 0

        # Some defaults to place character
        self.center_x = 126 * TILE_SCALING
        self.center_y = self.height * 1.25 - 10

    def die(self):
        self.dying = True
        self.set_hit_box([[-0, -0], [0, -0], [0, 0]])
        self.change_x = 0
        self.change_y = -1

    def update_animation(self, delta_time: float = 1 / 60):
        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Jumping animation
        if self.change_y >= 0.2:
            self.texture = self.walk_textures[2][self.character_face_direction]
            return
        elif self.dying or self.change_y <= -1:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            return

        # Idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Walking animation
        if self.update_walk == 5:  # Update frame only every 5 cycles
            self.cur_texture += 1
            if self.cur_texture > 2:
                self.cur_texture = 0
            self.texture = self.walk_textures[self.cur_texture][
                self.character_face_direction
            ]
            self.update_walk = 0
        self.update_walk += 1


def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
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
        arcade.draw_rectangle_filled(
            self.center_x, self.center_y, RECT_WIDTH, RECT_HEIGHT, RECT_COLOR
        )
