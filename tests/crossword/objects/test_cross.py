
import unittest
import pytest
from crossword.objects import Cross
from crossword.objects import WordSpace


class TestCross(unittest.TestCase):

    def test_init(self):
        word_space1 = WordSpace((2, 1), 3, 'vertical')
        word_space2 = WordSpace((1, 2), 3, 'horizontal')
        cross = Cross(word_space1, word_space2)

        assert hasattr(cross, "word_space_horizontal")
        assert hasattr(cross, "word_space_vertical")
        assert cross.word_space_horizontal == word_space2
        assert cross.word_space_vertical == word_space1

        assert cross.index_in_horizontal == 1
        assert cross.index_in_vertical == 1

        assert cross.coordinates == (2, 2)

    def test_id(self):
        word_space1 = WordSpace((2, 1), 3, 'vertical')
        word_space2 = WordSpace((1, 2), 3, 'horizontal')
        cross = Cross(word_space1, word_space2)

        assert cross.id() == "C_2_2"
