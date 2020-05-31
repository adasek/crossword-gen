#!/usr/bin/env python3
import re
import random
import itertools


class Cross:
    def __init__(self, word_space1, word_space2):
        self.word_space_horizontal = None
        self.word_space_vertical = None
        self.coordinates = None

        if word_space1.type == 'horizontal' and word_space2.type == 'vertical':
            self.word_space_horizontal = word_space1
            self.word_space_vertical = word_space2
        elif word_space1.type == 'vertical' and word_space2.type == 'horizontal':
            self.word_space_vertical = word_space1
            self.word_space_horizontal = word_space2
        else:
            raise Exception("Bad types")

        # Compute coordinates
        cross_coordinates = set(self.word_space_vertical.spaces()).intersection(
            set(self.word_space_horizontal.spaces()))
        if len(cross) > 1:
            raise Exception("Non Euclidian crossword")
        elif len(cross) == 0:
            raise Exception("Incoherent cross")
        else:
            self.coordinates = cross_coordinates.pop()

    def id(self):
        return f"C_{self.coordinates[0]}_{self.coordinates[1]}"

    def other(self, word_space):
        if word_space == self.word_space_vertical:
            return self.word_space_horizontal
        elif word_space == self.word_space_horizontal:
            return self.word_space_vertical
        else:
            raise Exception("Bad call of other", self, word_space, self.word_space_horizontal, self.word_space_vertical)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.coordinates == other.coordinates

    def __str__(self):
        return f"Cross at {self.coordinates} between {self.word_space_horizontal} and {self.word_space_vertical}"


class CharList:
    def __init__(self, char_list):
        self.char_list = char_list
        self.length = len(self.char_list)
        self._iter_counter = 0

    def __iter__(self):
        self._iter_counter = 0
        return self

    def __next__(self):
        if self._iter_counter < self.length:
            result = self.char_list[self._iter_counter]
            self._iter_counter += 1
            return result
        else:
            raise StopIteration

    def __getitem__(self, index):
        return self.char_list[index]

    def __str__(self):
        return "".join(self.char_list)

    def __hash__(self):
        return hash("/".join(self.char_list))

    def __eq__(self, other):
        return self.char_list == other.char_list

class Word(CharList):
    id = 1

    def __init__(self, word_string):
        word_as_list = list(word_string)
        CharList.__init__(self, word_as_list)
        self.use = 1 # probability it will be used
        self.id = Word.id
        Word.id += 1


class Mask(object):
    # Immutable, https://stackoverflow.com/a/4828108
    __slots__ = ["length", "mask"]

    def __init__(self, spaces, crosses):
        super(Mask, self).__setattr__("length", len(spaces))
        # print(f"Creating mask of {len(spaces)} with {spaces} and:")
        # for cross in crosses:
        #    print(f"  {cross}")

        mask_list = []
        for space in spaces:
            space_cross = [cross for cross in crosses if cross.coordinates == space]
            if len(space_cross) == 0:
                mask_list.append(False)
            elif len(space_cross) == 1:
                mask_list.append(True)
            elif len(space_cross) > 1:
                raise Exception("Multiple crosses")
        super(Mask, self).__setattr__("mask", mask_list)

    def __hash__(self):
        return hash(self.mask_string())

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.mask == other.mask

    def __str__(self):
        return self.mask_string()

    def mask_string(self):
        mask_string = ""
        for applied in self.mask:
            if applied:
                mask_string += "X"
            else:
                mask_string += "."
        return mask_string

    # Returns relevant chars
    def apply_word(self, word):
        applied = []

        for crossed, char in zip(self.mask, word):
            if crossed:
                applied.append(char)
        return CharList(applied)


class WordSpace:
    counter = 1

    def __init__(self, start, length, type):
        self.start = start
        self.length = length
        self.type = type
        self.crosses = []
        self.occupied_by = None
        self.my_counter = WordSpace.counter
        WordSpace.counter += 1

    def id(self):
        return f"WS_{self.my_counter}"

    def occupy(self, word):
        if word.length != self.length:
            print(self)
            print(word)
            raise Exception("Length of word does not correspond with WordSpace")
        self.occupied_by = word

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
        return f"word_space_fill('{self.mask()}', [{crosses_string}], '{self.id()}')."

    def add_cross(self, other_word_space):
        new_cross = Cross(self, other_word_space)
        if new_cross.coordinates not in self.spaces():
            raise Exception("Tried to add cross not in spaces")
        if new_cross in self.crosses:
            raise Exception("Tried to add already present cross", self.crosses)
        self.crosses.append(new_cross)

    def mask(self):
        return Mask(self.spaces(), self.crosses)

    def my_char_on_cross(self, cross):
        return self.occupied_by[self.index_of_cross(cross)]

    # Zero indexed!
    def index_of_cross(self, cross):
        for index, space in enumerate(self.spaces(), start=0):
            if cross.coordinates == space:
                return index
        raise Exception("Cross not found")

    def apply_other_words(self):
        applied = []

        for cross in self.crosses:
            applied.append(cross.other(self).my_char_on_cross(cross))
        return CharList(applied)

    def char_at(self, x, y):
        if (x, y) not in self.spaces():
            return None
        return self.occupied_by[self.spaces().index((x, y))]

    def __str__(self):
        describing_string = f"{self.type.capitalize()} WordSpace starting at {self.start} of length {self.length}"
        if self.occupied_by:
            describing_string += f" occupied by {self.occupied_by}"
        return describing_string


# Load words
words = list()
with open('wordlist.dat', 'r') as fp:
    for word_string in fp.readlines():
        words.append(Word(re.sub(r'[\r\n\t]*', '', word_string)))

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
        word_length = x - in_word
        if char == '_' and in_word < 0:
            in_word = x
        elif char != '_' and in_word >= 0:
            if word_length > 1:
                # flush word
                word_spaces.append(WordSpace((in_word, y), word_length, 'horizontal'))
            in_word = -1
    # flush last word
    word_length = len(line) - in_word + 1
    if in_word >= 0 and word_length > 1:
        word_spaces.append(WordSpace((in_word, y), word_length, 'horizontal'))

for x in range(1, 1 + max([len(line) for line in crossword])):
    in_word = -1
    for y, line in enumerate(crossword, start=1):
        char = 'X'
        try:
            char = line[x - 1]
        except IndexError:
            char = 'X'
        word_length = y - in_word
        if char == '_' and in_word < 0:
            in_word = y
        elif char != '_' and in_word >= 0:
            if word_length > 1:
                # flush word
                word_spaces.append(WordSpace((x, in_word), word_length, 'vertical'))
            in_word = -1
    # flush last word
    word_length = len(crossword) - in_word + 1
    if in_word >= 0 and word_length > 1:
        word_spaces.append(WordSpace((x, in_word), word_length, 'vertical'))

# Compute all crosses between word_spaces - O(N^2) can be improved
for word_space_pair in itertools.product(word_spaces, repeat=2):
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

word_spaces_vertical = [w for w in word_spaces if w.type == 'vertical']
word_spaces_horizontal = [w for w in word_spaces if w.type == 'horizontal']

# for word_space in word_spaces:
#    print(word_space)
#    print(word_space.mask())

# Structure words #2: split by all known masks
# Currently only masks of word_spaces_horizontal are needed
# Example usage: words_by_masks['..XX.']['ab'] =>
words_by_masks = {}
possible_masks = set([word_space.mask() for word_space in word_spaces])

for word in words:
    for mask in possible_masks:
        if mask.length == word.length:
            chars = mask.apply_word(word)
            if mask not in words_by_masks:
                words_by_masks[mask] = {}
            if chars not in words_by_masks[mask]:
                words_by_masks[mask][chars] = set()
            words_by_masks[mask][chars].add(word)

print("Data parsing complete.")

# Prolog output
with open("prolog_output/words.pl", "w") as words_prolog:
    for word in words:
            print(f"word({word.id},'{word}').", file=words_prolog)

    for word in words:
            print(f"usable_word({word.id}, {word.use}).", file=words_prolog)

with open("prolog_output/word_masks.pl", "w") as word_masks_prolog:
    for mask in possible_masks:
        for chars in words_by_masks[mask]:
            # word_space('x...x', ['c','t'],'cukat')
            for word in words_by_masks[mask][chars]:
                chars_string = "','".join(chars)
                print(f"word_mask('{mask}', ['{chars_string}'], {word.id}).", file=word_masks_prolog)
            #words_by_masks[mask][chars]

with open("prolog_output/word_space_names.pl", "w") as word_space_names:
    for word_space in word_spaces:
        print(f"word_space_name('{word_space.id()}').", file=word_space_names)

with open("prolog_output/word_space_fills.pl", "w") as word_space_fills:
    for word_space in word_spaces:
        print(f"{word_space.to_prolog()}", file=word_space_fills)


print("--------")

