import types
import unittest

import pandas as pd
import pytest

from crossword.objects import Word, WordList, WordSpace


class TestWordSpace(unittest.TestCase):

    def test_find_best_options2(self):
        word_space1 = WordSpace((2, 1), 3, 'vertical')
        word_space2 = WordSpace((1, 3), 3, 'horizontal')
        word_space1.add_cross(word_space2)
        word_space2.add_cross(word_space1)

        # [Word("abc"), Word("bcd")]
        words1 = pd.DataFrame([
            ('abc', 'Test abc', 1),
            ('bcd', 'Test bcd', 2)
            ], columns=['word_label_text', 'word_description_text', 'word_concept_id'])


        word_list1 = WordList(words1, language="en")
        word_space1.bind(Word("abc"))
        assert len(word_space1.get_half_bound_crosses()) == 1
        result = word_space1.find_best_options(word_list1)
        assert len(result) == 1

