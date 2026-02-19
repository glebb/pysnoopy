import arcade
from dataclasses import dataclass
from typing import Callable, Optional

class LevelHook:
    def __init__(self):
        self.physics_engine: Optional[arcade.PhysicsEnginePlatformer] = None
        self.speed_multiplier = 1.0
        self.level_bounds: tuple[float, float, float, float] | None = None

    def update(self):
        pass

    def draw(self):
        pass

    def draw_hit_boxes(self):
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


def get_default_levels() -> list[LevelSpec]:
    return [
        LevelSpec(name="Level 1", map_path="../assets/level1.json"),
        LevelSpec(
            name="Level 2",
            map_path="../assets/level2.json",
            required_object_names=("moving_hazard",),
        ),
        LevelSpec(name="Level 3", map_path="../assets/level3.json"),
        LevelSpec(
            name="Level 4",
            map_path="../assets/level4.json",
            required_object_names=("moving_hazard",),
        ),
        LevelSpec(
            name="Level 5",
            map_path="../assets/level5.json",
            required_object_names=("moving_hazard",),
        ),
        LevelSpec(
            name="Level 6",
            map_path="../assets/level6.json",
            required_object_names=("moving_hazard",),
        ),
    ]
