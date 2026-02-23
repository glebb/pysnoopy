import arcade
from typing import TypeAlias

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
    def __init__(self, *, scale: float | tuple[float, float] | None = None):
        super().__init__()

        self.character_face_direction = RIGHT_FACING

        self.cur_texture = 0
        self.scale = CHARACTER_SCALING if scale is None else scale

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
        self.texture_hit_boxes: dict[int, list[tuple[float, float]]] = {}
        self._build_texture_hit_box_cache()
        self.hit_box = arcade.hitbox.RotatableHitBox(
            self.texture_hit_boxes[id(self.texture)]
        )

        self.change_x = 0
        self.update_walk = 0

        # Some defaults to place character
        self.center_x = PLAYER_START_X
        self.center_y = PLAYER_START_Y

    def _set_texture(self, texture):
        if self.texture is texture:
            return
        previous_hit_box_bottom = self.center_y + min(
            point[1] for point in self.hit_box.points
        )
        self.texture = texture
        self._sync_hit_box_with_direction()
        new_hit_box_bottom = min(point[1] for point in self.hit_box.points)
        self.center_y = previous_hit_box_bottom - new_hit_box_bottom

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

    def _build_texture_hit_box_cache(self):
        texture_pairs = [
            self.idle_texture_pair,
            self.jump_texture_pair,
            self.fall_texture_pair,
            *self.walk_textures,
        ]
        for texture_pair in texture_pairs:
            for texture in texture_pair:
                self.texture_hit_boxes[id(texture)] = self._build_scaled_hit_box(texture)

    def _sync_hit_box_with_direction(self):
        self.hit_box = arcade.hitbox.RotatableHitBox(
            self.texture_hit_boxes[id(self.texture)]
        )

    def die(self):
        self.dying = True
        self.jumping = False
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


DEFAULT_ITEM_WIDTH = 50
DEFAULT_ITEM_HEIGHT = 50
DEFAULT_ITEM_COLOR = arcade.color.DARK_BROWN
ColorTuple: TypeAlias = tuple[int, int, int] | tuple[int, int, int, int]


class Item(arcade.Sprite):
    def __init__(
        self,
        width: float = DEFAULT_ITEM_WIDTH,
        height: float = DEFAULT_ITEM_HEIGHT,
        color: ColorTuple = DEFAULT_ITEM_COLOR,
    ):
        super().__init__()

        # Set up attribute variables

        # Where we are
        self.center_x = 0
        self.center_y = 0

        # Where we are going
        self.change_x = 0
        self.change_y = 0
        self.rect_width = float(width)
        self.rect_height = float(height)
        self.rect_color = color
        self.hit_box = arcade.hitbox.RotatableHitBox(
            self._build_rect_hit_box(self.rect_width, self.rect_height)
        )
        self.bounds: tuple[float, float, float, float] = (
            self.rect_width / 2,
            SCREEN_WIDTH - self.rect_width / 2,
            self.rect_height / 2,
            SCREEN_HEIGHT - self.rect_height / 2,
        )

    def _build_rect_hit_box(self, width: float, height: float):
        half_width = width / 2
        half_height = height / 2
        return [
            (-half_width, -half_height),
            (-half_width, half_height),
            (half_width, half_height),
            (half_width, -half_height),
        ]

    def set_size(self, width: float, height: float):
        self.rect_width = max(1.0, float(width))
        self.rect_height = max(1.0, float(height))
        self.hit_box = arcade.hitbox.RotatableHitBox(
            self._build_rect_hit_box(self.rect_width, self.rect_height)
        )

    def set_bounds(self, bounds: tuple[float, float, float, float] | None):
        if bounds is None:
            return
        left, right, bottom, top = bounds
        self.bounds = (
            left + self.rect_width / 2,
            right - self.rect_width / 2,
            bottom + self.rect_height / 2,
            top - self.rect_height / 2,
        )

    def update(self):
        # Move the rectangle
        self.center_x += self.change_x
        self.center_y += self.change_y
        left_bound, right_bound, bottom_bound, top_bound = self.bounds
        # Check if we need to bounce of right edge
        if self.center_x > right_bound:
            self.change_x *= -1
        # Check if we need to bounce of top edge
        if self.center_y > top_bound:
            self.change_y *= -1
        # Check if we need to bounce of left edge
        if self.center_x < left_bound:
            self.change_x *= -1
        # Check if we need to bounce of bottom edge
        if self.center_y < bottom_bound:
            self.change_y *= -1

    def draw(self):
        # Draw the rectangle
        arcade.draw_lbwh_rectangle_filled(
            self.center_x - self.rect_width / 2,
            self.center_y - self.rect_height / 2,
            self.rect_width,
            self.rect_height,
            self.rect_color,
        )


class TriangleHazard(arcade.Sprite):
    def __init__(
        self,
        width: float = DEFAULT_ITEM_WIDTH,
        height: float = DEFAULT_ITEM_HEIGHT,
        color: ColorTuple = arcade.color.BLACK,
    ):
        super().__init__()

        # Create a texture for the sprite so it renders correctly in a SpriteList
        image = arcade.Texture.create_empty(
            f"triangle_{width}_{height}_{color}",
            (int(width), int(height))
        ).image
        
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        draw.polygon(
            [(0, height), (width / 2, 0), (width, height)],
            fill=color
        )
        self.texture = arcade.Texture(image)
        
        self.center_x = 0
        self.center_y = 0
        self.change_x = 0
        self.change_y = 0
        self.rect_width = float(width)
        self.rect_height = float(height)
        self.rect_color = color
        self.hit_box = arcade.hitbox.RotatableHitBox(
            self._build_triangle_hit_box(self.rect_width, self.rect_height)
        )
        self.bounds: tuple[float, float, float, float] = (
            self.rect_width / 2,
            SCREEN_WIDTH - self.rect_width / 2,
            self.rect_height / 2,
            SCREEN_HEIGHT - self.rect_height / 2,
        )

    def _build_triangle_hit_box(self, width: float, height: float):
        half_width = width / 2
        half_height = height / 2
        return [
            (-half_width, -half_height),
            (0, half_height),
            (half_width, -half_height),
        ]

    def set_size(self, width: float, height: float):
        self.rect_width = max(1.0, float(width))
        self.rect_height = max(1.0, float(height))
        self.hit_box = arcade.hitbox.RotatableHitBox(
            self._build_triangle_hit_box(self.rect_width, self.rect_height)
        )

    def set_bounds(self, bounds: tuple[float, float, float, float] | None):
        if bounds is None:
            return
        left, right, bottom, top = bounds
        # Allow the hazard to fully exit the screen before wrapping
        self.bounds = (
            left - self.rect_width / 2,
            right + self.rect_width / 2,
            bottom + self.rect_height / 2,
            top - self.rect_height / 2,
        )

    def update(self):
        self.center_x += self.change_x
        self.center_y += self.change_y
        left_bound, right_bound, bottom_bound, top_bound = self.bounds
        
        # Wrap around horizontally
        if self.change_x < 0 and self.center_x < left_bound:
            self.center_x = right_bound
        elif self.change_x > 0 and self.center_x > right_bound:
            self.center_x = left_bound
