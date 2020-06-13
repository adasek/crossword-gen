import unittest
import pytest
from crossword.objects import WordSpace, Word, WordList
import types


class TestWordSpace(unittest.TestCase):

    def test_find_best_options2(self):
        word_space1 = WordSpace((2, 1), 3, 'vertical')
        word_space2 = WordSpace((1, 3), 3, 'horizontal')
        word_space1.add_cross(word_space2)
        word_space2.add_cross(word_space1)

        words1 = [Word("abc"), Word("bcd")]
        word_list1 = WordList(words1, [word_space1, word_space2])
        word_space1.bind(Word("abc"))
        assert len(word_space1.get_half_bound_crosses()) == 1
        result = word_space1.find_best_options2(word_list1)
        assert len(result) == 1

