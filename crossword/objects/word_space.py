import itertools
import json
import math
import random
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd

from .charlist import CharList
from .cross import Cross
from .mask import Mask
from .word import Word
from .word_list import WordList


class WordSpace:
    """Single line of characters in crossroad that will be filled with a word"""
    counter = 1

    def __init__(self, start: Tuple[int, int], length: int, direction: str):
        """Constuct WordSpace without any word"""
        self.failed_words_index_set = set()
        self.crosses = []
        self.occupied_by = None
        self.my_counter = WordSpace.counter
        self.possibility_matrix = None
        self.start = start
        self.length = length
        self.type = direction
        WordSpace.counter += 1

    def reset_failed_words(self):
        self.failed_words_index_set = set()

    def build_possibility_matrix(self, word_list: WordList):
        # possible_words number for letter x cross
        self.possibility_matrix = np.zeros(shape=(len(self.crosses), len(word_list.alphabet)))
        self.rebuild_possibility_matrix(word_list)

    def rebuild_possibility_matrix(self, word_list):
        for cross_index, cross in enumerate(self.crosses):
            if not cross.bound_value():
                for char_index, char in word_list.alphabet_with_index():
                    other_ws = cross.other(self)
                    mask, mask_chars = other_ws.mask_with(cross, char)
                    self.possibility_matrix[cross_index, char_index] = word_list.word_count(mask, mask_chars)

    def id(self) -> str:
        """Prolog identifer of this object"""
        return f"WS_{self.my_counter}"

    def bind(self, word: Word):
        """Add the word into WordSpace"""
        affected = []
        if word.length != self.length:
            print(self)
            print(word)
            raise Exception(f"Length of word does not correspond with WordSpace {word} {word.length} != {self.length}")

        for cross in self.crosses:
            if not cross.bound_value():
                affected.append(cross.other(self))

        self.occupied_by = word

        return affected


    def unbind(self):
        """Remove binded word from WordSpace"""
        affected = []
        self.occupied_by = None
        for cross in self.crosses:
            if not cross.bound_value():
                affected.append(cross.other(self))
        return affected

    def bindable(self, word_list: WordList) -> pd.DataFrame:
        """List all words that can be filled to WordSpace at this moment"""
        mask, chars = self.mask_current()
        return word_list.words(mask, chars, failed_index=self.failed_words_index_set)

    def get_unbounded_crosses(self) -> List[Cross]:
        """List crosses that don't have certain Char bound.
        Will return empty list if word is bind to this WordSpace"""
        return [cross for cross in self.crosses if not cross.bound_value()]

    def get_half_bound_crosses(self) -> List[Cross]:
        """List crosses that do have at least one word bounded"""
        return [cross for cross in self.crosses if cross.is_half_bound() or not cross.bound_value()]

    def solving_priority(self, word_list: WordList, crossing_aggregate: str, letter_aggregate: str, unbound: int = 0) -> int:
        unbounded_crosses = self.get_unbounded_crosses()
        if len(unbounded_crosses) == 0:
            # This is a must have word!
            return unbound

        data = self.count_candidate_crossings(word_list, letter_aggregate=letter_aggregate)
        if crossing_aggregate == 'sum':
            return np.sum(data)
        elif crossing_aggregate == 'max':
            return np.max(data)
        elif crossing_aggregate == 'min':
            return np.min(data)
        elif crossing_aggregate == 'mean':
            return np.mean(data)
        else:
            raise "Unknown crossing_aggregate"

    def count_candidate_crossings(self, word_list: WordList, letter_aggregate: str):
        crosses_list = [False if cross.bound_value() else True for cross in self.crosses]

        if letter_aggregate == 'sum':
            transform = self.possibility_matrix.sum(axis=1)
        elif letter_aggregate == 'max':
            transform = self.possibility_matrix.max(axis=1)
        elif letter_aggregate == 'min':
            transform = self.possibility_matrix.min(axis=1)
        elif letter_aggregate == 'mean':
            transform = self.possibility_matrix.mean(axis=1)
        else:
            raise "Unknown letter_aggregate"

        return [val[1] for val in zip(crosses_list, transform.transpose().tolist()) if val[0] is True]


    def find_best_options(self, word_list: WordList):
        unbounded_crosses = self.get_half_bound_crosses()
        #if self._best_options is not None and self._best_options_unbouded_crosses == unbounded_crosses and self._best_options_unbouded_crosses:
        #    return self._best_options
        # mask ...X.
        candidate_char_dict_array = []
        for cross_index, cross in enumerate(unbounded_crosses):
            other_wordspace = cross.other(self)
            other_wordspace_mask, other_wordspace_chars = other_wordspace.mask_current()
            base_set = word_list.words_indices(other_wordspace_mask, other_wordspace_chars)
            if other_wordspace_mask.is_fully_bound():
                candidate_char_dict_array.append({cross.bound_value(): 1})
                continue
            other_wordspace_index = other_wordspace.index_of_cross(cross)
            mask_list = [False] * other_wordspace.length
            mask_list[other_wordspace_index] = True
            one_mask = Mask(mask_list)

            candidate_chars = []
            for char in word_list.alphabet:
                suitable_words_index = base_set.intersection(word_list.words_indices(one_mask, CharList([char]))).difference(other_wordspace.failed_words_index_set)
                words_count = len(suitable_words_index)
                if words_count > 0:
                    candidate_chars.append({'char': char, 'count': words_count})
            if len(candidate_chars) == 0:
                return None
            sorted_candidate_char_records = sorted(candidate_chars, key=lambda rec: rec['count'], reverse=True)
            candidate_char_dict_array.append({obj['char']: obj['count'] for obj in sorted_candidate_char_records})

        words_dataframe = self.bindable(word_list)

        #with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.max_colwidth', None):
        #    print(words_dataframe)

        cross_chars = []
        for cross in unbounded_crosses:
            index = cross.cross_index(self)
            char_col = words_dataframe['word_split'].apply(lambda x: x[index] if len(x) > index else None)
            cross_chars.append(char_col.values)

            char_matrix = np.column_stack(cross_chars)

        # Create score matrix by mapping characters to scores
        score_matrix = np.zeros_like(char_matrix, dtype=float)
        for cross_idx, char_dict in enumerate(candidate_char_dict_array):
            # Vectorized character-to-score mapping
            char_col = char_matrix[:, cross_idx]
            scores = np.array([char_dict.get(char, 0) for char in char_col])
            score_matrix[:, cross_idx] = scores

        # Zero out entire rows where any character has score 0
        zero_mask = (score_matrix == 0).any(axis=1)
        score_matrix[zero_mask] = 0

        # Calculate total scores (sum across crosses for each word)
        total_scores = score_matrix.sum(axis=1)

        if total_scores.size == 0:
            return []
        max_score = total_scores.max()
        if max_score > 0:
            best_indices = np.where(total_scores == max_score)[0]
            best_words = words_dataframe.iloc[best_indices]['word_split'].tolist()
        else:
            best_words = []
        return best_words

    def find_best_option(self, word_list: WordList):
        best_options = self.find_best_options(word_list)
        if best_options is not None and len(best_options) > 0:
            #if len(best_options) > 10:
            #    print(f"find_best_option {len(best_options)}")
            best_options = sorted(best_options, key=lambda word: 0 if np.isnan(word.get_score()) else word.get_score(), reverse=True)
            # rnd = random.choice(best_options)
            return best_options[0]
        else:
            # print(f"find_best_option: None")
            return None

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

    # Current mask with append given cross
    def mask_with(self, cross, word_char):
        mask, chars = self.mask_current()
        new_index = self.index_of_cross(cross)
        mask_list = mask.mask
        char_list = []
        char_counter = 0
        for index, val in enumerate(mask_list):
            if index == new_index:
                if val:
                    raise Exception("Assertion failed")
                mask_list[index] = True
                char_list.append(word_char)
            else:
                if val:
                    char_list.append(chars[char_counter])
                    char_counter += 1
        return Mask(mask_list), CharList(char_list)

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

    def to_json(self, export_occupied_by=False):
        return {
            'start': self.start,
            'length': self.length,
            'type': self.type,
            'occupied_by': self.occupied_by.to_json() if self.occupied_by is not None and export_occupied_by else None,
            'meaning': self.occupied_by.description if self.occupied_by is not None else None
        }

