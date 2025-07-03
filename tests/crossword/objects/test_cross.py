import unittest

from crossword.objects import Cross, Direction, WordSpace


class TestCross(unittest.TestCase):

    def test_init(self):
        word_space1 = WordSpace((2, 1), 3, Direction.VERTICAL)
        word_space2 = WordSpace((1, 2), 3, Direction.HORIZONTAL)
        cross = Cross(word_space1, word_space2)

        assert hasattr(cross, "word_space_horizontal")
        assert hasattr(cross, "word_space_vertical")
        assert cross.word_space_horizontal == word_space2
        assert cross.word_space_vertical == word_space1

        assert cross.index_in_horizontal == 1
        assert cross.index_in_vertical == 1

        assert cross.coordinates == (2, 2)
