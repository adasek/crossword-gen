from crossword.objects import Mask, CharList, Word
import pandas as pd
from crossword.objects.language import alphabet_set
from crossword.objects.language import split
import time

class WordList:
    """Data structure to effectively find suitable words"""
    counter = 1

    def __init__(self, words_df: pd.DataFrame, language: str, word_spaces):
        self.words_df = words_df
        self.alphabet = alphabet_set(language)

        # Add column with word length into words_df
        self.words_df.insert(loc=len(self.words_df.columns),
                             column='word_length',
                             value=self.words_df.loc[:, 'word_label_text'].map(
                                 lambda word: len(split(word.lower(),
                                                        locale_code=language))))
        self.words_structure = {}
        self.word_indices_by_length_set = {}
        self.words_by_index = {}
        for i in sorted(self.words_df.loc[:, 'word_length'].unique()):
            # self.words_df_by_length[i] = self.words_df.loc[self.words_df['word_length'] == i]
            # create X..  .X. ..X combinations
            self.word_indices_by_length_set[i] = set()
            self.words_structure[i] = {}
            for n in range(0, i):
                self.words_structure[i][n] = {}
                for char in alphabet_set():
                    self.words_structure[i][n][char] = set()
        for word_index, row in self.words_df.iterrows():
            word = split(row['word_label_text'].lower(), locale_code=language)
            word_len = len(word)
            self.word_indices_by_length_set[word_len].add(word_index)
            for char_index, char in enumerate(word):
                self.words_structure[word_len][char_index][char].add(word_index)

            self.words_by_index[word_index] = Word(row['word_label_text'], row['word_description_text'], index=word_index, language=language, score=row['score'])

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

    def alphabet_with_index(self):
        return enumerate(self.alphabet, start=0)

    def char_index(self, char):
        for index, ch in enumerate(self.alphabet):
            if ch == char:
                return index
        return -1

    def word_count(self, mask, chars):
        return len(self.words(mask, chars))

    def words(self, mask, chars, failed_index=None):
        if mask.length not in self.words_structure:
            raise Exception('No word suitable for the given space')

        word_index_set = None
        if mask.bind_count() == 0:
            word_index_set = self.word_indices_by_length_set[mask.length]
        chars_index = 0
        for mask_index, is_masked in enumerate(mask.mask):
            if is_masked:
                char = chars[chars_index]
                if word_index_set is None:
                    word_index_set = self.words_structure[mask.length][mask_index][char]
                else:
                    word_index_set = word_index_set.intersection(self.words_structure[mask.length][mask_index][char])

                chars_index += 1

        if word_index_set is None:
            # empty
            word_index_set = set()

        if failed_index is not None:
            word_index_set = word_index_set.difference(failed_index)
        return word_index_set
        #return self.words_df.loc[word_index_set]

    def get_word_by_index(self, word_index: int):
        return self.words_by_index[word_index]