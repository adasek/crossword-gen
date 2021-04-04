import re
from pathlib import Path
import itertools
from . import WordSpace
import json


class Crossword():
    def __init__(self, word_spaces):
        self.word_spaces = word_spaces
        self.width = None
        self.height = None

    def __str__(self):
        string = ""

        string += "--------\n"
        for y in range(1, self.height + 1):
            for x in range(1, self.width + 1):
                char = None

                # find relevant wordspaces (2 or 1)
                associated_word_spaces = []
                for word_space in self.word_spaces:
                    if (x, y) in word_space.spaces():
                        associated_word_spaces.append(word_space)

                if len(associated_word_spaces) > 2:
                    raise Exception("Char with >2 Wordspaces", x, y)
                elif len(associated_word_spaces) == 0:
                    char = ':'
                else:
                    # Check both crossed wordspaces have equal char
                    char = None
                    not_bound_count = 0
                    for ws in associated_word_spaces:
                        if ws.occupied_by is not None and char is not None and char != ws.char_at(x, y):
                            string += f"{ws.char_at(x, y)}"
                            raise Exception("Incoherent WordSpaces", x, y)
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

    def to_json(self, export_occupied_by=False):
        return json.dumps({
            'width': self.width,
            'height': self.height,
            'word_spaces': list(map(lambda ws: ws.to_json(export_occupied_by=export_occupied_by), self.word_spaces))
        })

    @staticmethod
    def from_grid(crossword_grid_file):
        crossword = Crossword([])
        grid = crossword.parse_crossword(crossword_grid_file)
        crossword.load_word_spaces_from_grid(grid)
        crossword.add_crosses()

        return crossword

    def parse_crossword(self, crossword_file):
        if self.width is not None or self.height is not None:
            raise Exception('init function called on non empty Crossword')
        # Load crossword as text
        grid = [['X_'], ['X_']]
        with open(crossword_file, 'r') as fp:
            crossword = [re.sub(r'[^_X]', '', line) for line in fp.readlines()]

        self.width = max([len(line) for line in crossword])
        self.height = len(crossword)

        return [x for x in crossword if len(x) > 0]

    def load_word_spaces_from_grid(self, crossword_grid):

        # Parse crossword to list of Words
        # horizontal: parse lines
        word_spaces = []
        for y, line in enumerate(crossword_grid, start=1):
            in_word = None
            for x, char in enumerate(line + "X", start=1):
                if char == '_' and in_word is None:
                    # word start
                    in_word = x
                elif char != '_' and in_word is not None:
                    word_length = x - in_word
                    if word_length > 1:
                        # flush word
                        word_spaces.append(WordSpace((in_word, y), word_length, 'horizontal'))
                    in_word = None


        for x in range(1, 1 + max([len(line) for line in crossword_grid])):
            in_word = -1
            for y, line in enumerate(crossword_grid, start=1):
                char = line[x - 1]
                word_length = y - in_word
                if char == '_' and in_word < 0:
                    in_word = y
                elif char != '_' and in_word >= 0:
                    if word_length > 1:
                        # flush word
                        word_spaces.append(WordSpace((x, in_word), word_length, 'vertical'))
                    in_word = -1
            # flush last word
            word_length = len(crossword_grid) - in_word + 1
            if in_word >= 0 and word_length > 1:
                word_spaces.append(WordSpace((x, in_word), word_length, 'vertical'))

        self.word_spaces = word_spaces
        return self.word_spaces

    # Compute all crosses between word_spaces - O(N^2) can be improved
    # The crosses are bound to existing word_spaces
    def add_crosses(self):
        for word_space in self.word_spaces:
            if len(word_space.crosses) > 0:
                raise "Crossword has some crosses generated"

        for word_space_pair in itertools.product(self.word_spaces, repeat=2):
            # Do only vertical->horizontal
            if word_space_pair[0].type == word_space_pair[1].type or word_space_pair[0].type == 'horizontal':
                continue
            cross = set(word_space_pair[0].spaces()).intersection(set(word_space_pair[1].spaces()))
            if len(cross) > 1:
                raise Exception("Non Euclidian crossword")
            elif len(cross) == 0:
                continue
            else:
                # found one cross
                word_space_pair[0].add_cross(word_space_pair[1])
                word_space_pair[1].add_cross(word_space_pair[0])
        return
