""" Tools for reinforcement learning applied to 2048. """
from typing import List
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
                 img_size: int = 128) -> None:
        """ Constructor.

        :param path:     path to chromedriver
        :type  path:     str
        :param headless: run browser headless or not, defaults to False
        :type  headless: bool, optional
        :param img_size: desired game board screenshot size, defaults to 128
        :type  img_size: int, optional
        """
        options = Options()
        if headless:
            options.add_argument('--headless')
        super(Game2048, self).__init__(path, options=options)
        self.actions = [
            ActionChains(self).send_keys(Keys.UP),
            ActionChains(self).send_keys(Keys.LEFT),
            ActionChains(self).send_keys(Keys.DOWN),
            ActionChains(self).send_keys(Keys.RIGHT)]
        self.img_size = img_size
        self.get('https://2048game.com/')

    def __enter__(self):
        """ Open browser and game. """
        super(Game2048, self).__enter__()
        return self

    def act(self, idx: int) -> None:
        """ Execute a game command: up, left, own, right.

        :param idx: index of action to perform:
        type   idx: int
        """
        self.actions[idx].perform()

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
                        tile = self.find_element_by_class_name(tile_class)
                        tile_num = int(tile.text)
                        state[row][col] = tile_num
                    except NoSuchElementException:
                        break
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

    def game_is_over(self) -> bool:
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

    def restart(self) -> None:
        """ Restarts the game if the game is over; otherwise error. """
        self.find_element_by_class_name('retry-button').click()

    def take_tile_screenshot(self) -> Image:
        """ Take a screenshot of the 16-tile game board.

        :return: screenshot
        :rtype:  Image
        """
        tiles = self.find_element_by_class_name('grid-container')
        pseudofile = BytesIO(tiles.screenshot_as_png)
        return Image.open(pseudofile).resize((self.img_size, self.img_size))
