from pathlib import Path
from crossword.objects import Word, WordSpace
import re
import itertools

class Parser(object):
    def __init__(self, directory):
        self.directory = Path(directory)
        self.words = []
        self.words_by_len = {}

    def parse_original_wordlist(self, original_wordlist_file):
        with open(original_wordlist_file) as fp:
            lines = fp.readlines()

            self.words = [Word(line.split('/')[0].lower().strip()) for line in lines]
        return self.words

    def parse_words(self):
        # Load words
        self.words = []
        with open(Path(self.directory, wordlist_file), 'r') as fp:
            for word_string in fp.readlines():
                self.words.append(Word(re.sub(r'[\r\n\t]*', '', word_string)))

        return self.words

    def words_by_length(self):
        # Structure words #1: do split by lengths:
        self.words_by_len = {}
        for word in self.words:
            length = word.length
            if length not in self.words_by_len:
                self.words_by_len[length] = []
            self.words_by_len[length].append(word)

        return(self.words_by_len)

    def parse_crossword(self, crossword_file):
        # Load crossword as text
        crossword = [['X_'], ['X_']]
        with open(Path(self.directory, crossword_file), 'r') as fp:
            crossword = [re.sub(r'[^_X]', '', line) for line in fp.readlines()]

        return [x for x in crossword if len(x) > 0]

    def parse_word_spaces(self, crossword):

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

        return word_spaces

    # Compute all crosses between word_spaces - O(N^2) can be improved
    def add_crosses(self, word_spaces):
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

        return

    def create_possible_masks(self, word_spaces, generate_children_threshold=0):
        possible_masks = set()
        for word_space in word_spaces:
            if word_space.mask() not in possible_masks:
                if generate_children_threshold > 0:
                    possible_masks.update(word_space.masks_all(generate_children_threshold))
                else:
                    possible_masks.add(word_space.mask())

        return possible_masks

    def create_words_by_masks(self, words, possible_masks):
        words_by_masks = {}
        for index, word in enumerate(words):
            for mask in possible_masks:
                if mask.length == word.length:
                    chars = mask.apply_word(word)
                    if mask not in words_by_masks:
                        words_by_masks[mask] = {}
                    if chars not in words_by_masks[mask]:
                        words_by_masks[mask][chars] = set()
                    words_by_masks[mask][chars].add(word)
            #if index % 100 == 0:
            #    print(f"{index}/{len(words)}")

        return words_by_masks
