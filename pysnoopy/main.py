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
    from pysnoopy.views import GameView, TitleView
else:
    from .globals import SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH
    from .views import GameView, TitleView


def _parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Run pySNOOPY")
    parser.add_argument(
        "--start-level",
        type=int,
        default=1,
        help="Start directly from level number N (1-based).",
    )
    args = parser.parse_args(argv)
    if args.start_level < 1:
        parser.error("--start-level must be >= 1")
    return args


def main(argv: list[str] | None = None):
    args = _parse_args(argv)
    file_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(file_path)

    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    setattr(window, "run_speed_multiplier", 1.0)
    setattr(window, "start_level", args.start_level)

    start_view: arcade.View
    if args.start_level > 1:
        start_view = GameView(start_level=args.start_level)
    else:
        start_view = TitleView()

    window.show_view(start_view)
    start_view.setup()
    music_sound = arcade.load_sound('../assets/sound/entertainer.wav', streaming=False)
    setattr(window, "music_sound", music_sound)
    setattr(
        window,
        "music_player",
        arcade.play_sound(
        music_sound,
        volume=0.5,
        loop=True,
        speed=float(getattr(window, "run_speed_multiplier", 1.0)),
    ),
    )
    arcade.set_background_color(arcade.color.WHITE_SMOKE)

    arcade.run()


if __name__ == "__main__":
    main()
