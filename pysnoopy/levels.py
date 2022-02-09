import arcade
from sprites import Item


class BaseLevel:
    def __init__(self):
        self.name = "Name"
        self.map = "map"
        self.physics_engine: arcade.PhysicsEnginePlatformer = None

    def update(self):
        pass

    def draw(self):
        pass
    
    def setup(self, physics_engine):
        self.physics_engine = physics_engine


class Level_1(BaseLevel):
    def __init__(self):
        self.name = "Level 1"
        self.map = "../assets/level1.json"

class Level_2(BaseLevel):
    def __init__(self):
        self.name = "Level 2"
        self.map = "../assets/level2.json"
        self.item = Item()
        self.item.center_x = 200
        self.item.center_y = 300
        self.item.change_x = 2
        self.item.change_y = 3

    def update(self):
        self.item.update()

    def draw(self):
        self.item.draw()
