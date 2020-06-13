from crossword.objects import Mask, CharList, Word

class WordList:
    """Data structure to effectively find suitable words"""
    counter = 1

    def __init__(self, words, word_spaces):
        self.word_list = {}
        self.words_by_lengths = {}
        self.words_by_lengths_list = {}  # Used for index search to compatibility matrix

        self.alphabet = set()
        for word in words:
            self.alphabet.update(word.char_list)

        lengths = set([word.length for word in words])
        for len in lengths:
            self.words_by_lengths[len] = set([word for word in words if word.length == len])
            self.words_by_lengths_list[len] = [word for word in words if word.length == len]

        self.one_masks = self.create_one_masks(word_spaces)
        self.words_by_masks = self.create_words_by_masks(words, self.one_masks)

    def words_of_length(self, length):
        return self.words_by_lengths_list[length]

    def create_one_masks(self, word_spaces):
        possible_masks = set()
        for word_space in word_spaces:
            possible_masks.update(word_space.one_masks())

        return possible_masks

    def create_words_by_masks(self, words, possible_masks):
        words_by_masks = {}
        for index, word in enumerate(words):
            for mask in possible_masks:
                if mask.length == word.length:
                    chars = mask.apply_word(word)
                    if mask not in words_by_masks.keys():
                        words_by_masks[mask] = {}
                    if chars not in words_by_masks[mask].keys():
                        words_by_masks[mask][chars] = set()
                    words_by_masks[mask][chars].add(word)

        return words_by_masks

    def word_by_index(self, length, index):
        return self.words_by_lengths_list[length][index]

    def char_index(self, char):
        for index, ch in enumerate(self.alphabet):
            if ch == char:
                return index
        return -1

    def words(self, mask: Mask, chars: CharList):
        if isinstance(chars, Word):
            chars = CharList(chars.char_list)

        if not isinstance(chars, CharList):
            raise Exception("words type mismatch")
        if not isinstance(mask, Mask):
            raise Exception("mask type mismatch")

        division_masks = mask.divide(chars)
        words = None
        if mask.bind_count() == 0:
            return self.words_by_lengths[mask.length]
        for division_mask in division_masks:
            mask = division_mask[0]
            char = division_mask[1]
            try:
                division_words = self.words_by_masks[mask][char]
            except KeyError:
                division_words = set()
            if words is not None:
                words = words.intersection(division_words)
            else:
                words = division_words
        return words

    def word_count(self, mask, chars):
        return len(self.words(mask, chars))
