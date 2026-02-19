import arcade
from typing import Optional, cast

from .sprites import PlayerCharacter
from .sprites import Item


class BaseLevel:
    def __init__(self):
        self.name = "Name"
        self.map = "map"
        self.physics_engine: Optional[arcade.PhysicsEnginePlatformer] = None
        self.speed_multiplier = 1.0

    def update(self):
        pass

    def draw(self):
        pass

    def draw_hit_boxes(self):
        pass

    def setup(self, physics_engine):
        self.physics_engine = physics_engine

    def set_speed_multiplier(self, multiplier: float):
        self.speed_multiplier = multiplier


class Level_1(BaseLevel):
    def __init__(self):
        super().__init__()
        self.name = "Level 1"
        self.map = "../assets/level1.json"


class Level_2(BaseLevel):
    def __init__(self):
        super().__init__()
        self.name = "Level 2"
        self.map = "../assets/level2.json"
        self.item = Item()
        self.item_start_x = 200
        self.item_start_y = 300
        self.item_speed_x = 2
        self.item_speed_y = 3
        self.item.center_x = self.item_start_x
        self.item.center_y = self.item_start_y
        self.item.change_x = self.item_speed_x
        self.item.change_y = self.item_speed_y

    def setup(self, physics_engine):
        super().setup(physics_engine)
        self.item.center_x = self.item_start_x
        self.item.center_y = self.item_start_y
        self.item.change_x = self.item_speed_x * self.speed_multiplier
        self.item.change_y = self.item_speed_y * self.speed_multiplier

    def update(self):
        self.item.update()
        if self.physics_engine is None:
            return

        player_sprite = cast(PlayerCharacter, self.physics_engine.player_sprite)
        if player_sprite.collides_with_sprite(self.item):
            player_sprite.die()

    def draw(self):
        self.item.draw()

    def draw_hit_boxes(self):
        self.item.draw_hit_box()


class Level_3(BaseLevel):
    def __init__(self):
        super().__init__()
        self.name = "Level 3"
        self.map = "../assets/level3.json"
