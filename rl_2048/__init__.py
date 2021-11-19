""" Tools for reinforcement learning applied to 2048. """
from typing import List, Tuple
import os
import time
from pathlib import Path
from io import BytesIO
from PIL import Image
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException)


class Game2048(Chrome):
    """ Interface for a reinforcement learning agent to play 2048. """
    def __init__(self,
                 path: str,
                 headless: bool = False,
                 height: int = 600,
                 width: int = 500,
                 img_size: int = 128) -> None:
        """ Constructor.

        :param path:     path to chromedriver
        :type  path:     str
        :param headless: run browser headless or not, defaults to False
        :type  headless: bool, optional
        :param height:   window height in pixels, defaults to 500
        :type  height:   int, optional
        :param width:    window width in pixels, defaults to 500
        :type  width:    int, optional
        :param img_size: game board screenshot size in pixels, defaults to 128
        :type  img_size: int, optional
        """
        options = Options()
        if headless:
            options.add_argument('--headless')
        super(Game2048, self).__init__(path, options=options)

        # store vars
        self.path = path
        self.headless = headless
        self.height = height
        self.width = width
        self.img_size = img_size

        # misc setup
        self.set_window_size(width, height)  # if too small screenshot cropped
        self.actions = [
            ActionChains(self).send_keys(Keys.UP),
            ActionChains(self).send_keys(Keys.LEFT),
            ActionChains(self).send_keys(Keys.DOWN),
            ActionChains(self).send_keys(Keys.RIGHT)]

        # load game files
        game_path = Path(os.path.dirname(__file__)) / 'game' / 'index.html'
        self.get('file:///' + str(game_path))

    def __enter__(self):
        """ Open browser and game. """
        super(Game2048, self).__enter__()
        return self

    def __repr__(self) -> str:
        """ Representation.

        :return: Game instantiation settings
        :rtype:  str
        """
        return ''.join([
            'Game2048(',
            f'path="{self.path}", ',
            f'headless={self.headless}, ',
            f'height={self.height}, ',
            f'width={self.width}, ',
            f'img_size={self.img_size}'
            ')'])

    def step(self,
             action: int,
             delay: float = 0.5) -> Tuple[object, float, bool, dict]:
        """ Advance the environment based on agent action.

        :param action: up (0), left (1), down (2), right (3)
        :type  action: int
        :param delay:  seconds to wait for game to update, defaults to 0.5
        :type  delay:  float, optional
        :return:       state, reward, whether game over, debug info
        :rtype:        Tuple[object, float, bool, dict]
        """
        prev_score = self.get_score()
        self.actions[action].perform()
        time.sleep(delay)
        state = self.get_state()
        reward = self.get_score() - prev_score
        done = self.is_over()
        return state, reward, done, {}

    def get_state(self) -> List[List[int]]:
        """ Get the numbers in the 16-tile game board.

        :return: game board tiles
        :rtype:  List[List[int]]
        """
        state = [[0] * 4 for _ in range(4)]
        for row in range(4):
            for col in range(4):
                # look for a specific tile at some row and col (1-index)
                tile_class = f'tile-position-{col + 1}-{row + 1}'
                tile_num = None
                while tile_num is None:
                    try:
                        tiles = self.find_elements_by_class_name(tile_class)
                        if len(tiles) == 0:
                            tile_num = 0
                        elif len(tiles) == 1:
                            tile_num = int(tiles[0].text)
                        else:
                            for t in tiles:
                                if 'merged' in t.get_attribute('class'):
                                    tile_num = int(t.text)
                                    break
                        state[row][col] = tile_num
                    except ValueError:
                        pass  # need to wait for game to stabilize
                    except StaleElementReferenceException:
                        pass  # need to wait for game to stabilize
        return state

    def get_score(self) -> int:
        """ Get the current game score.

        :return: game score
        :rtype: int
        """
        score = self.find_element_by_class_name('score-container')
        score_text = score.text  # will also include children text

        # remove child text if it exists
        # --actions that increase game score create a child that shows the amt
        # --otherwise the game removes the elem
        try:
            addition = score.find_element_by_class_name('score-addition')
            addition_text = addition.text
            score_text = score_text.replace(addition_text, '')
        except NoSuchElementException:
            pass

        return int(score_text)

    def is_over(self) -> bool:
        """ Check if game is in game over state.
            One sign is whether or not a specific div is class 'game-over'.

        :return: whether or not the game is in game over state
        :rtype:  bool
        """
        status = None
        try:
            self.find_element_by_class_name('game-over')
            status = True
        except NoSuchElementException:
            status = False
        return status

    def reset(self, delay: float = 0.5) -> object:
        """ Starts a new game.

        :param delay: seconds to wait for game to reload, defaults to 0.5
        :type  delay: float, optional
        :return:      initial state
        :rtype:       object
        """
        self.find_element_by_class_name('restart-button').click()
        time.sleep(delay)
        return self.get_state()

    def take_screenshot(self) -> Image:
        """ Take a screenshot of the 16-tile game board.

        :return: screenshot
        :rtype:  Image
        """
        tiles = self.find_element_by_class_name('grid-container')
        pseudofile = BytesIO(tiles.screenshot_as_png)
        return Image.open(pseudofile).resize((self.img_size, self.img_size))
