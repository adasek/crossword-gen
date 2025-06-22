import pandas as pd

from .language import alphabet_set, split
from .mask import Mask
from .word import Word


class WordList:
    """Data structure to effectively find suitable words"""
    counter = 1

    def __init__(self, words_df: pd.DataFrame, language: str):
        self.words_df = words_df
        self.alphabet = alphabet_set(language)

        # Add column with word length into words_df
        self.words_df.insert(loc=len(self.words_df.columns),
                             column='word_length',
                             value=self.words_df.loc[:, 'word_label_text'].map(
                                 lambda word_str: len(split(word_str.lower(),
                                                            locale_code=language))))
        self.words_df['word_split'] = None

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
                for char in alphabet_set(language):
                    self.words_structure[i][n][char] = set()
        for word_index, row in self.words_df.iterrows():
            word = split(row['word_label_text'].lower(), locale_code=language)
            word_len = len(word)
            self.word_indices_by_length_set[word_len].add(word_index)
            for char_index, char in enumerate(word):
                self.words_structure[word_len][char_index][char].add(word_index)

            if 'score' in row:
                word_score = row['score']
            else:
                word_score = None
            word = Word(row['word_label_text'], row['word_description_text'],
                        index=word_index,
                        language=language,
                        score=word_score,
                        word_list=self,
                        word_concept_id=row['word_concept_id'])
            self.words_by_index[word_index] = word
            self.words_df.at[word_index, 'word_split'] = word
            for index, char in enumerate(word):
                if f'word_split_char_{index}' not in self.words_df.columns:
                    self.words_df[f'word_split_char_{index}'] = None
                self.words_df.at[word_index, f'word_split_char_{index}'] = char

    def use_score_vector(self, score_vector):
        self.words_df.drop([x for x in ['score'] if x in self.words_df.columns], axis=1, inplace=True)
        self.words_df = self.words_df.join(score_vector, on='word_concept_id', how='left', rsuffix='_right')
        # for word_index, row in self.words_df.iterrows():
        #    self.words_by_index[word_index].score = row['score']

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
        return len(self.words_indices(mask, chars))

    def words(self, mask: Mask, chars: list[str], failed_index: bool = None) -> pd.DataFrame:
        return self.words_df.loc[self.words_df.index.intersection(self.words_indices(mask, chars, failed_index))]

    def words_indices(self, mask, chars, failed_index=set()):
        if mask.length not in self.words_structure:
            raise Exception(f"No word suitable for the given space (length {mask.length})")

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

        if len(failed_index) == 0:
            return word_index_set
        else:
            return word_index_set.difference(failed_index)

    def candidate_char_dict(self, words_indices_list: list[int], char_index: int):
        filtered_df = self.words_df.iloc[words_indices_list]
        return filtered_df[f"word_split_char_{char_index}"].value_counts().to_dict()

    def get_word_by_index(self, word_index: int):
        return self.words_by_index[word_index]

    def get_words_by_indices(self, word_indices: list):
        return [self.words_by_index[index] for index in word_indices if index in self.words_by_index]
