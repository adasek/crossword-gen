import copy
import itertools
import json
import re
from pathlib import Path
from typing import Optional

import numpy as np

from .word_list import WordList
from .word_space import Direction, WordSpace


class Crossword:
    """Represents a crossword puzzle with its dimensions and word spaces."""

    def __init__(self, word_spaces: list[WordSpace], grid_file: Optional[Path] = None):
        self.word_spaces = word_spaces
        self.width: Optional[int] = None
        self.height: Optional[int] = None
        self.grid_file = grid_file

    def __str__(self):
        string = ""

        string += "--------\n"
        for y in range(1, self.height + 1):
            for x in range(1, self.width + 1):
                # find relevant wordspaces (2 or 1)
                associated_word_spaces = []
                for word_space in self.word_spaces:
                    if (x, y) in word_space.spaces():
                        associated_word_spaces.append(word_space)

                if len(associated_word_spaces) > 2:
                    raise ValueError("Char with >2 Wordspaces", x, y)

                if len(associated_word_spaces) == 0:
                    char = ':'
                else:
                    # Check both crossed wordspaces have equal char
                    char = None
                    not_bound_count = 0
                    for ws in associated_word_spaces:
                        if ws.occupied_by is not None and char is not None and char != ws.char_at(x, y):
                            string += f"{ws.char_at(x, y)}"
                            raise ValueError("Incoherent WordSpaces", x, y)
                        if ws.occupied_by is not None:
                            char = ws.char_at(x, y)
                        else:
                            not_bound_count += 1

                    if not char:
                        # both unbounded
                        char = ' '

                string += char
            string += "\n"
        return string

    def as_json(self, export_occupied_by=False):
        """Exports the crossword to a JSON-compatible dictionary."""
        return {
            'width': self.width,
            'height': self.height,
            'word_spaces': list(map(lambda ws: ws.to_json(export_occupied_by=export_occupied_by), self.word_spaces))
        }

    def to_json(self, export_occupied_by=False):
        """Converts the crossword to a JSON string."""
        return json.dumps(self.as_json(export_occupied_by))

    def get_copy(self):
        """Returns a deep copy of the crossword."""
        return copy.deepcopy(self)

    @staticmethod
    def from_grid(crossword_grid_file: Path) -> 'Crossword':
        """Creates a Crossword object from a grid file."""
        crossword = Crossword([], crossword_grid_file)
        grid = crossword.parse_crossword(crossword_grid_file)
        crossword.load_word_spaces_from_grid(grid)
        crossword.add_crosses()

        return crossword

    def parse_crossword(self, crossword_file: Path) -> list[str]:
        """Parses a crossword file and returns the grid as a list of strings."""
        if self.width is not None or self.height is not None:
            raise ValueError('init function called on non empty Crossword')
        # Load crossword as text
        with open(crossword_file, 'r', encoding="utf-8") as fp:
            crossword = [re.sub(r'[^ _X]', '', line) for line in fp.readlines()]

        self.width = max(len(line) for line in crossword)
        self.height = len(crossword)

        return [x for x in crossword if len(x) > 0]

    @staticmethod
    def from_grid_object(grid_object):
        """
        Creates a crossword from a grid.
        """
        crossword = Crossword([])
        grid = crossword.parse_grid_object(grid_object)
        crossword.load_word_spaces_from_grid(grid)
        crossword.add_crosses()
        return crossword

    def parse_grid_object(self, grid_object):
        """ Parses a grid object and returns the grid as a list of strings."""
        self.width = grid_object['width']
        self.height = grid_object['height']
        return ["".join([grid_object['bitmap'][self.width*y+x] for x in range(self.width)]) for y in range(self.height)]

    def load_word_spaces_from_grid(self, crossword_grid: list[str]):
        """ Loads word spaces from the crossword grid."""

        # Parse crossword to list of Words
        # horizontal: parse lines
        word_spaces = []
        for y, line in enumerate(crossword_grid, start=1):
            in_word = None
            for x, char in enumerate(line + "X", start=1):
                if char in ['_', ' '] and in_word is None:
                    # word start
                    in_word = x
                elif char not in ['_', ' '] and in_word is not None:
                    word_length = x - in_word
                    if word_length > 1:
                        # flush word
                        word_spaces.append(WordSpace((in_word, y), word_length, Direction.HORIZONTAL))
                    in_word = None

        for x in range(1, 1 + max(len(line) for line in crossword_grid)):
            in_word = -1
            for y, line in enumerate(crossword_grid, start=1):
                char = line[x - 1]
                word_length = y - in_word
                if char in ['_', ' '] and in_word < 0:
                    in_word = y
                elif char not in ['_', ' '] and in_word >= 0:
                    if word_length > 1:
                        # flush word
                        word_spaces.append(WordSpace((x, in_word), word_length, Direction.VERTICAL))
                    in_word = -1
            # flush last word
            word_length = len(crossword_grid) - in_word + 1
            if in_word >= 0 and word_length > 1:
                word_spaces.append(WordSpace((x, in_word), word_length, Direction.VERTICAL))

        self.word_spaces = word_spaces
        return self.word_spaces

    def add_crosses(self) -> None:
        """
        Adds crosses to the crossword based on the word spaces.
        Compute all crosses between word_spaces - O(N^2) can be improved
        The crosses are bound to existing word_spaces
        """
        for word_space in self.word_spaces:
            if len(word_space.crosses) > 0:
                raise ValueError("Crossword has some crosses generated")

        for word_space_pair in itertools.product(self.word_spaces, repeat=2):
            # Do only vertical->horizontal
            if word_space_pair[0].direction == word_space_pair[1].direction or word_space_pair[0].is_horizontal():
                continue
            set_a = set(word_space_pair[0].spaces())
            set_b = set(word_space_pair[1].spaces())
            cross = set_a.intersection(set_b)
            if len(cross) > 1:
                raise ValueError("Non Euclidian crossword")

            if len(cross) == 0:
                continue

            # found one cross
            word_space_pair[0].add_cross(word_space_pair[1])
            word_space_pair[1].add_cross(word_space_pair[0])

    def is_success(self):
        """Check if all word spaces are occupied by words."""
        for ws in self.word_spaces:
            if ws.occupied_by is None:
                return False
        return True

    def evaluate_score(self):
        """Evaluate scores of all word spaces."""
        score = 0
        for ws in self.word_spaces:
            if not np.isnan(ws.occupied_by.get_score()):
                score += ws.occupied_by.get_score()
        return score

    def reset(self):
        """Reset the crossword to its initial state."""
        for word_space in self.word_spaces:
            word_space.unbind()
            word_space.reset_failed_words()

    def build_possibility_matrix(self, word_list: WordList) -> None:
        """Builds the possibility matrix for each word space using the provided word list."""
        for word_space in self.word_spaces:
            word_space.build_possibility_matrix(word_list)

    def __eq__(self, other):
        """Check if two crosswords are equal."""
        if not isinstance(other, Crossword):
            return False
        if self.width != other.width or self.height != other.height:
            return False
        if len(self.word_spaces) != len(other.word_spaces):
            return False
        for ws in self.word_spaces:
            if ws not in other.word_spaces:
                return False
        return True

    def __hash__(self):
        """Hash function for the crossword."""
        return hash((self.width, self.height, tuple(self.word_spaces)))
