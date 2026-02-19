from dataclasses import dataclass
from typing import Any

import arcade


@dataclass
class GameState:
    start_level: int = 1
    run_speed_multiplier: float = 1.0
    music_sound: arcade.Sound | None = None
    music_player: Any | None = None

    def restart_music(self, speed: float | None = None):
        if self.music_sound is None:
            return
        if speed is not None:
            self.run_speed_multiplier = speed
        if self.music_player is not None:
            self.music_sound.stop(player=self.music_player)
        self.music_player = arcade.play_sound(
            self.music_sound,
            volume=0.5,
            loop=True,
            speed=self.run_speed_multiplier,
        )
