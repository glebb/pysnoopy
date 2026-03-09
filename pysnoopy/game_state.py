from dataclasses import dataclass, field
from typing import Any

import arcade

from .globals import (
    GRAVITY,
    MUSIC_SPEED_MULTIPLIER_STEP,
    MUSIC_SPEED_MULTIPLIER_START,
    PLAYER_JUMP_SPEED,
    PLAYER_MOVEMENT_SPEED,
    RUN_SPEED_MULTIPLIER_STEP,
)


@dataclass(frozen=True)
class GlobalRealitySettings:
    """Global base physics/logic constants for the whole game.

    These settings define the immutable baseline "reality" and must not change
    during gameplay.
    """

    gravity: float = GRAVITY
    player_movement_speed: float = PLAYER_MOVEMENT_SPEED
    player_jump_speed: float = PLAYER_JUMP_SPEED


@dataclass
class RoundSettings:
    """Run-wide settings that persist across levels within a round."""

    run_speed_multiplier: float = 1.0
    music_speed_multiplier: float = MUSIC_SPEED_MULTIPLIER_START


@dataclass
class LevelRuntimeSettings:
    """Per-level runtime modifiers.

    These are rebuilt on every level setup (including death restart) and must
    never be carried to another level.
    """

    run_speed_multiplier: float = 1.0
    move_speed_multiplier: float = 1.0
    jump_speed_multiplier: float = 1.0
    gravity_multiplier: float = 1.0
    hazard_speed_multiplier: float = 1.0


@dataclass
class GameState:
    start_level: int = 1
    starting_speed_rounds: int = 0
    round_settings: RoundSettings = field(default_factory=RoundSettings)
    reality_settings: GlobalRealitySettings = field(default_factory=GlobalRealitySettings)
    music_sound: arcade.Sound | None = None
    music_player: Any | None = None

    def __post_init__(self) -> None:
        self._apply_starting_round_speed()

    @property
    def run_speed_multiplier(self) -> float:
        return self.round_settings.run_speed_multiplier

    @property
    def music_speed_multiplier(self) -> float:
        return self.round_settings.music_speed_multiplier

    def reset_for_new_run(self) -> None:
        self.round_settings = RoundSettings()
        self._apply_starting_round_speed()

    def _apply_starting_round_speed(self) -> None:
        for _ in range(self.starting_speed_rounds):
            self.advance_round(
                run_speed_step=RUN_SPEED_MULTIPLIER_STEP,
                music_speed_step=MUSIC_SPEED_MULTIPLIER_STEP,
            )

    def advance_round(self, run_speed_step: float, music_speed_step: float) -> None:
        self.round_settings.run_speed_multiplier *= run_speed_step
        self.round_settings.music_speed_multiplier *= music_speed_step

    def restart_music(self, speed: float | None = None):
        if self.music_sound is None:
            return
        if speed is not None:
            self.round_settings.music_speed_multiplier = speed
        if self.music_player is not None:
            self.music_sound.stop(player=self.music_player)
        self.music_player = arcade.play_sound(
            self.music_sound,
            volume=0.5,
            loop=True,
            speed=self.round_settings.music_speed_multiplier,
        )
