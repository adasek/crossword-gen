from crossword.objects import Cross
from crossword.objects import Mask
from crossword.objects import Word
from crossword.objects import WordList

import math
from typing import List, Set, Dict, Tuple


class WordSpace:
    """Single line of characters in crossroad that will be filled with a word"""
    counter = 1

    def __init__(self, start: Tuple[int, int], length: int, direction: str):
        """Constuct WordSpace without any word"""
        self.start = start
        self.length = length
        self.type = direction
        self.crosses = []
        self.occupied_by = None
        self.my_counter = WordSpace.counter
        WordSpace.counter += 1

    def id(self) -> str:
        """Prolog identifer of this object"""
        return f"WS_{self.my_counter}"

    def bind(self, word: Word):
        """Add the word into WordSpace"""
        if word.length != self.length:
            print(self)
            print(word)
            raise Exception("Length of word does not correspond with WordSpace")
        self.occupied_by = word

    def unbind(self):
        """Remove binded word from WordSpace"""
        self.occupied_by = None

    def bindable(self, word_list: WordList) -> Set[Word]:
        """List all words that can be filled to WordSpace at this moment"""
        mask, chars = self.mask_current()
        return word_list.words(mask, chars)

    def get_unbounded_crosses(self) -> List[Cross]:
        """List crosses that don't have certain Char bound.
        Will return empty list if word is bind to this WordSpace"""
        return [cross for cross in self.crosses if not cross.bound_value()]

    def expectation_value(self, word_list: WordList) -> int:
        """Count how many words may be filled to the unbound WordSpace crossing this.
        Will return +inf if no unbound WordSpace is crossing"""
        possible_words = self.bindable(word_list)
        if len(possible_words) == 0:
            return 0
        # For every bindable option compute the potential candidates
        unbounded_crosses = self.get_unbounded_crosses()
        if len(unbounded_crosses) == 0:
            # This is a must have word!
            return math.inf
        # Try to fill in any word
        return max([self.count_promising(word_list, unbounded_crosses, word) for word in possible_words])

    def count_promising(self, word_list: WordList, unbounded_crosses, word):
        promising = 0
        for cross in unbounded_crosses:
            try:
                char = word[self.index_of_cross(cross)]
            except:
                print(f"{word} ... {self.index_of_cross(cross)}")
                raise Exception("wtf")
            mask, mask_chars = cross.other(self).mask_current(cross, char)
            try:
                possible_count = word_list.word_count(mask, mask_chars)
            except KeyError:
                possible_count = 0
            promising += possible_count
            if possible_count == 0:
                return 0
        return promising

    def find_best_option(self, word_list: WordList, option_number=0):
        unbounded_crosses = self.get_unbounded_crosses()
        possible_words = sorted(self.bindable(word_list),
                                key=lambda word: self.count_promising(word_list, unbounded_crosses, word),
                                reverse=True)
        if option_number >= len(possible_words):
            return None
        else:
            return possible_words[option_number]

    # Returns set of tuples - positions that this words goes through
    def spaces(self):
        spaces = list()
        if self.type == 'horizontal':
            for x in range(self.start[0], self.start[0] + self.length):
                spaces.append((x, self.start[1]))
        elif self.type == 'vertical':
            for y in range(self.start[1], self.start[1] + self.length):
                spaces.append((self.start[0], y))
        else:
            raise Exception("Unknown WordSpace type")
        return spaces

    def to_prolog(self):
        crosses_string = ", ".join([c.id() for c in self.crosses])
        return f"word_space_fill(\"{self.mask()}\", [{crosses_string}], \"{self.id()}\")"

    def add_cross(self, other_word_space):
        new_cross = Cross(self, other_word_space)
        if new_cross.coordinates not in self.spaces():
            raise Exception("Tried to add cross not in spaces")
        if new_cross in self.crosses:
            raise Exception("Tried to add already present cross", self.crosses)
        self.crosses.append(new_cross)

    def mask(self):
        return Mask(self.spaces(), self.crosses)

    # Returns currently binded mask, optionally with one more bounded char (at given cross)
    def mask_current(self, add_cross=None, add_char=''):
        mask_list = [False] * self.length
        char_list = [None] * self.length
        for cross in self.crosses:
            if cross.bound_value():
                mask_list[self.index_of_cross(cross)] = True
                char_list[self.index_of_cross(cross)] = cross.bound_value()
        if add_cross:
            mask_list[self.index_of_cross(add_cross)] = True
            char_list[self.index_of_cross(add_cross)] = add_char

        return Mask(mask_list), Word([ch for ch in char_list if ch])

    # All possible combinations of masks derived from the main mask
    # example: X..X. generates X.... and ...X.
    def masks_all(self, treshold):
        mask = self.mask()
        if mask.bind_count() <= treshold:
            return mask.all_derivations()
        else:
            return [mask]

    # All masks with 1
    def one_masks(self):
        masks = []
        for cross in self.crosses:
            mask_list = [False] * self.length
            mask_list[cross.cross_index(self)] = True
            masks.append(Mask(mask_list))
        return masks

    def masks_prefix(self):
        return self.mask().prefix_derivations()

    def my_char_on_cross(self, cross):
        if not self.occupied_by:
            return None
        return self.occupied_by[self.index_of_cross(cross)]

    # Zero indexed!
    def index_of_cross(self, cross):
        return cross.cross_index(self)

    def apply_other_words(self):
        applied = []

        for cross in self.crosses:
            applied.append(cross.other(self).my_char_on_cross(cross))
        return Word(applied)

    def char_at(self, x, y):
        if (x, y) not in self.spaces():
            return None
        return self.occupied_by[self.spaces().index((x, y))]

    def check_crosses(self):
        for cross in self.crosses:
            a = self.char_at(cross.coordinates[0], cross.coordinates[1])
            b = cross.other(self).char_at(cross.coordinates[0], cross.coordinates[1])
            if a != b:
                return False
        return True

    # Generates mask that covers good crosses
    # and resets crosses good status
    def good_mask(self):
        mask = Mask(self.spaces(), [cross for cross in self.crosses if not cross.good])
        for cross in self.crosses:
            cross.good = True
        return mask

    def unbind_incompatible_crosswords(self):
        for cross in self.crosses:
            other = cross.other(self)
            if other.occupied_by and other.char_at(cross.coordinates[0], cross.coordinates[1]) !=\
                    self.char_at(cross.coordinates[0], cross.coordinates[1]):
                other.unbind()

    def __str__(self):
        describing_string = f"{self.type.capitalize()} WordSpace starting at {self.start} of length {self.length}"
        if self.occupied_by:
            describing_string += f" occupied by {self.occupied_by}"
        return describing_string