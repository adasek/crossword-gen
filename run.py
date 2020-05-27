#!/usr/bin/env python3
import re
import random


class Cross:
    word_horizontal = None
    word_vertical = None

    def __init__(self, word1, word2):
        if word1.type == 'horizontal' and word2.type == 'vertical':
            self.word_horizontal = word1
            self.word_vertical = word2
        elif word1.type == 'vertical' and word2.type == 'horizontal':
            self.word_vertical = word1
            self.word_horizontal = word2
        else:
            raise Exception("Bad types")


class Word:
    word_string = ''
    length = 0
    _iter_counter = 0

    def __init__(self, word_string):
        self.word = word_string
        self.length = len(self.word)

    def __iter__(self):
        self._iter_counter = 0
        return self

    def __next__(self):
        if self._iter_counter < self.length:
            result = self.word[self._iter_counter]
            self._iter_counter += 1
            return result
        else:
            raise StopIteration


class Mask:
    mask = []
    length = 0

    def __init__(self, spaces, crossings):
        self.length = len(spaces)
        for space in spaces:
            space_crossing = [cross for cross in crossings if cross[0] == space[0] and cross[1] == space[1]]
            if len(space_crossing) == 0:
                self.mask.append(False)
            elif len(space_crossing) == 1:
                self.mask.append(True)
            elif len(space_crossing) > 1:
                raise Exception("Multiple crossings")

    def __hash__(self):
        return hash(self.mask_string())

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.mask == other.mask

    def __iter__(self):
        self._iter_counter = 0
        return self

    def __next__(self):
        if self._iter_counter < self.length:
            result = self.mask[self._iter_counter]
            self._iter_counter += 1
            return result
        else:
            raise StopIteration

    def mask_string(self):
        mask_string = ''
        for applied in self.mask:
            if applied:
                mask_string += 'X'
            else:
                mask_string += '.'
        return mask_string

    # Returns relevant chars
    def apply_word(self, word):
        applied_str = ''

        for crossed, char in zip(mask, word):
            if crossed:
                applied_str += char
        return applied_str


class WordSpace:
    length = 0
    crossings = set()
    type = 'horizontal'
    start = (0, 0)
    occupied_by = None

    def __init__(self, start, length, type):
        self.start = start
        self.length = length
        self.type = type

    def occupy(self, word):
        self.occupied_by = word

    # Returns set of tuples - positions that this words goes through
    def spaces(self):
        spaces = list()
        if self.type == 'horizontal':
            for x in range(self.start[0], self.start[0] + length):
                spaces.append((x, self.start[1]))
        elif self.type == 'vertical':
            for y in range(self.start[1], self.start[1] + length):
                spaces.append((self.start[0], y))
        else:
            raise Exception("Unknown WordSpace type")
        return spaces

    def add_crossing(self, crossing, other_word_space):
        self.crossings.add((crossing[0], crossing[1], other_word_space))

    def mask(self):
        spaces = self.spaces()
        crossings = self.crossings
        return Mask(spaces, crossings)


# Load words
words = list()
with open('wordlist.dat', 'r') as fp:
    for word_string in fp.readlines():
        words.append(Word(word_string))

# Structure words #1: do split by lengths:
words_by_length = {}
for word in words:
    length = word.length
    if length not in words_by_length:
        words_by_length[length] = []
    words_by_length[length].append(word)

# Load crossword as text
crossword = [['X_'], ['X_']]
with open('crossword.dat', 'r') as fp:
    crossword = [re.sub(r'[^_X]', '', line) for line in fp.readlines()]

# Parse crossword to list of Words
# horizontal: parse lines
word_spaces = []
for y, line in enumerate(crossword, start=1):
    in_word = -1
    for x, char in enumerate(line, start=1):
        if char == '_' and in_word < 0:
            in_word = x
        elif (char != '_' and in_word >= 0):
            # flush word
            word_spaces.append(WordSpace((in_word, y), x - in_word, 'horizontal'))
            in_word = -1
    # flush last word
    if in_word >= 0:
        word_spaces.append(WordSpace((in_word, y), len(line) - in_word + 1, 'horizontal'))

for x in range(1, 1 + max([len(line) for line in crossword])):
    in_word = -1
    for y, line in enumerate(crossword, start=1):
        char = 'X'
        try:
            char = line[x]
        except IndexError:
            char = 'X'
    if char == '_' and in_word < 0:
        in_word = y
    elif char != '_' and in_word >= 0:
        # flush word
        word_spaces.append(WordSpace((x, in_word), y - in_word, 'vertical'))
        in_word = -1
    if in_word >= 0:
        word_spaces.append(WordSpace((x, in_word), len(crossword) - in_word + 1, 'vertical'))

# Compute all crosses between word_spaces - O(N^2) can be improved
for word_space_a in word_spaces:
    for word_space_b in word_spaces:
        if word_space_a == word_space_b or word_space_a.type == word_space_b.type:
            continue
        cross = set(word_space_a.spaces).intersection(set(word_space_b.spaces))
        if len(cross) > 1:
            raise Exception("Non Euclidian crossword")
        elif len(cross) == 0:
            continue
        else:
            # found one crossing
            crossing = cross[0]
            word_space_a.add_crossing(crossing, word_space_b)
            word_space_b.add_crossing(crossing, word_space_a)

word_spaces_vertical = [w for w in word_spaces if w.type == 'vertical']
word_spaces_horizontal = [w for w in word_spaces if w.type == 'horizontal']

# Fill verticals on radom
for word_space in word_spaces_vertical:
    word_space.occupy(random.choice(words_by_length[word_space.length].random))

# Structure words #2: split by all known masks
# Currently only masks of word_spaces_horizontal are needed
# Example usage: words_by_masks['..XX.']['ab'] =>
words_by_masks = {}
possible_masks = set([word_space.mask() for word_space in word_spaces])

for word in words:
    for mask in possible_masks:
        chars = mask.apply_word(word)
        if mask not in words_by_masks:
            words_by_masks[mask] = {}
        if chars not in words_by_masks[mask]:
            words_by_masks[mask][chars] = set()
        words_by_masks[mask][chars].add(word)

print("Data parsing complete.")
print("--------")
