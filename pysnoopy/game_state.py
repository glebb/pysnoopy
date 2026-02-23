from dataclasses import dataclass
from typing import Any

import arcade

from .globals import MUSIC_SPEED_MULTIPLIER_START


@dataclass
class GameState:
    start_level: int = 1
    run_speed_multiplier: float = 1.0
    music_speed_multiplier: float = MUSIC_SPEED_MULTIPLIER_START
    music_sound: arcade.Sound | None = None
    music_player: Any | None = None

    def restart_music(self, speed: float | None = None):
        if self.music_sound is None:
            return
        if speed is not None:
            self.music_speed_multiplier = speed
        if self.music_player is not None:
            self.music_sound.stop(player=self.music_player)
        self.music_player = arcade.play_sound(
            self.music_sound,
            volume=0.5,
            loop=True,
            speed=self.music_speed_multiplier,
        )
