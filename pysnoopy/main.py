"""
pySNOOPY

"""
import argparse
import arcade
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from pysnoopy.globals import SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH
    from pysnoopy.game_state import GameState
    from pysnoopy.views import GameView, TitleView
else:
    from .globals import SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH
    from .game_state import GameState
    from .views import GameView, TitleView


def _parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Run pySNOOPY")
    parser.add_argument(
        "--start-level",
        type=int,
        default=None,
        help="Start directly from level number N (1-based).",
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=0,
        help="Apply the end-of-loop speed boost N times before starting.",
    )
    args = parser.parse_args(argv)
    if args.start_level is not None and args.start_level < 1:
        parser.error("--start-level must be >= 1")
    if args.speed < 0:
        parser.error("--speed must be >= 0")
    return args


def main(argv: list[str] | None = None):
    args = _parse_args(argv)
    file_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(file_path)
    start_level = 1 if args.start_level is None else args.start_level

    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_state = GameState(
        start_level=start_level,
        starting_speed_rounds=args.speed,
    )

    start_view: arcade.View
    if args.start_level is not None:
        start_view = GameView(game_state=game_state, start_level=start_level)
    else:
        start_view = TitleView(game_state=game_state)

    window.show_view(start_view)
    start_view.setup()
    game_state.music_sound = arcade.load_sound('../assets/sound/entertainer.wav', streaming=False)
    game_state.restart_music()
    arcade.set_background_color(arcade.color.WHITE_SMOKE)

    arcade.run()


if __name__ == "__main__":
    main()
