"""
pySNOOPY

"""
import arcade
import os

from globals import SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH
from views import TitleView, GameView


def main():
    file_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(file_path)

    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = TitleView()
    window.show_view(start_view)
    start_view.setup()
    music = arcade.load_sound('../assets/sound/entertainer.wav', streaming=False)
    music.play(volume=0.7, loop=True)
    arcade.set_background_color(arcade.color.WHITE_SMOKE)

    arcade.run()


if __name__ == "__main__":
    main()
