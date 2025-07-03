from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from crossword.objects import Cross, Direction, Word, WordList, WordSpace


class TestWordSpace:
    """Test suite for WordSpace class using modern pytest patterns."""

    @pytest.fixture
    def sample_words_df(self):
        """Sample DataFrame for WordList creation."""
        return pd.DataFrame([
            ('abc', 'Test abc', 1),
            ('bcd', 'Test bcd', 2),
            ('def', 'Test def', 3),
            ('xyz', 'Test xyz', 4),
            ('cat', 'Test cat', 5),
            ('dog', 'Test dog', 6),
        ], columns=['word_label_text', 'word_description_text', 'word_concept_id'])

    @pytest.fixture
    def word_list(self, sample_words_df):
        """WordList fixture for testing."""
        return WordList(sample_words_df, language="en")

    @pytest.fixture
    def horizontal_word_space(self):
        """Horizontal WordSpace fixture."""
        return WordSpace((1, 2), 3, Direction.HORIZONTAL)

    @pytest.fixture
    def vertical_word_space(self):
        """Vertical WordSpace fixture."""
        return WordSpace((2, 1), 3, Direction.VERTICAL)

    @pytest.fixture
    def crossed_word_spaces(self):
        """Pair of crossed WordSpaces."""
        ws1 = WordSpace((2, 1), 3, Direction.VERTICAL)
        ws2 = WordSpace((1, 3), 3, Direction.HORIZONTAL)
        ws1.add_cross(ws2)
        ws2.add_cross(ws1)
        return ws1, ws2

    def test_wordspace_initialization(self):
        """Test WordSpace initialization with various parameters."""
        ws = WordSpace((5, 10), 7, Direction.HORIZONTAL)

        assert ws.start == (5, 10)
        assert ws.length == 7
        assert ws.direction == Direction.HORIZONTAL
        assert ws.occupied_by is None
        assert ws.possibility_matrix is None
        assert ws.crosses == []
        assert ws.failed_words_index_list == []

    def test_wordspace_initialization_vertical(self):
        """Test WordSpace initialization with vertical direction."""
        ws = WordSpace((3, 4), 5, Direction.VERTICAL)

        assert ws.start == (3, 4)
        assert ws.length == 5
        assert ws.direction == Direction.VERTICAL
        assert ws.is_vertical()
        assert not ws.is_horizontal()

    def test_is_horizontal_vertical(self, horizontal_word_space, vertical_word_space):
        """Test direction checking methods."""
        assert horizontal_word_space.is_horizontal()
        assert not horizontal_word_space.is_vertical()

        assert vertical_word_space.is_vertical()
        assert not vertical_word_space.is_horizontal()

    def test_spaces_horizontal(self, horizontal_word_space):
        """Test spaces() method for horizontal WordSpace."""
        expected_spaces = [(1, 2), (2, 2), (3, 2)]
        assert horizontal_word_space.spaces() == expected_spaces

    def test_spaces_vertical(self, vertical_word_space):
        """Test spaces() method for vertical WordSpace."""
        expected_spaces = [(2, 1), (2, 2), (2, 3)]
        assert vertical_word_space.spaces() == expected_spaces

    def test_spaces_invalid_direction(self):
        """Test spaces() with invalid direction raises ValueError."""
        ws = WordSpace((0, 0), 3, Direction.HORIZONTAL)
        # Mock invalid direction
        ws.direction = "invalid"

        with pytest.raises(ValueError, match="Unknown WordSpace type"):
            ws.spaces()

    def test_bind_word_success(self, horizontal_word_space):
        """Test successful word binding."""
        word = Word("abc")

        # Mock a cross for testing affected spaces
        mock_cross = Mock()
        mock_cross.bound_value.return_value = None
        mock_cross.other.return_value = Mock()
        horizontal_word_space.crosses = [mock_cross]

        affected = horizontal_word_space.bind(word)

        assert horizontal_word_space.occupied_by == word
        assert len(affected) == 1
        assert affected[0] == mock_cross.other.return_value

    def test_bind_word_none_raises_error(self, horizontal_word_space):
        """Test binding None word raises ValueError."""
        with pytest.raises(ValueError, match="Won't bind None"):
            horizontal_word_space.bind(None)

    def test_bind_word_wrong_length_raises_error(self, horizontal_word_space):
        """Test binding word with wrong length raises ValueError."""
        word = Word("toolong")

        with pytest.raises(ValueError, match="Length of word does not correspond"):
            horizontal_word_space.bind(word)

    def test_unbind_word(self, horizontal_word_space):
        """Test unbinding word from WordSpace."""
        word = Word("abc")
        horizontal_word_space.occupied_by = word

        # Mock crosses
        mock_cross = Mock()
        mock_cross.bound_value.return_value = None
        mock_cross.other.return_value = Mock()
        horizontal_word_space.crosses = [mock_cross]

        affected = horizontal_word_space.unbind()

        assert horizontal_word_space.occupied_by is None
        assert horizontal_word_space in affected
        assert mock_cross.other.return_value in affected

    def test_add_cross_success(self, crossed_word_spaces):
        """Test successful cross addition."""
        ws1, ws2 = crossed_word_spaces

        assert len(ws1.crosses) == 1
        assert len(ws2.crosses) == 1
        assert isinstance(ws1.crosses[0], Cross)

    def test_add_cross_not_in_spaces_raises_error(self, horizontal_word_space):
        """Test adding cross not in spaces raises ValueError."""
        other_ws = WordSpace((10, 10), 3, Direction.VERTICAL)

        with pytest.raises(ValueError, match="Incoherent cross"):
            horizontal_word_space.add_cross(other_ws)

    def test_add_cross_already_present_raises_error(self, horizontal_word_space):
        """Test adding already present cross raises ValueError."""
        other_ws = WordSpace((2, 1), 3, Direction.VERTICAL)
        horizontal_word_space.add_cross(other_ws)

        with pytest.raises(ValueError, match="Tried to add already present cross"):
            horizontal_word_space.add_cross(other_ws)

    def test_my_char_on_cross_with_word(self, horizontal_word_space):
        """Test getting character at cross when word is bound."""
        word = Word("abc")
        horizontal_word_space.occupied_by = word

        mock_cross = Mock()
        horizontal_word_space.crosses = [mock_cross]

        with patch.object(horizontal_word_space, '_index_of_cross', return_value=1):
            char = horizontal_word_space.my_char_on_cross(mock_cross)
            assert char == 'b'

    def test_my_char_on_cross_without_word(self, horizontal_word_space):
        """Test getting character at cross when no word is bound."""
        mock_cross = Mock()
        char = horizontal_word_space.my_char_on_cross(mock_cross)
        assert char is None

    def test_char_at_success(self, horizontal_word_space):
        """Test getting character at specific coordinates."""
        word = Word("abc")
        horizontal_word_space.occupied_by = word

        char = horizontal_word_space.char_at(2, 2)
        assert char == 'b'

    def test_char_at_invalid_coordinates_raises_error(self, horizontal_word_space):
        """Test getting character at invalid coordinates raises ValueError."""
        word = Word("abc")
        horizontal_word_space.occupied_by = word

        with pytest.raises(ValueError, match="Coordinates .* not in WordSpace"):
            horizontal_word_space.char_at(10, 10)

    def test_char_at_no_word_raises_error(self, horizontal_word_space):
        """Test getting character when no word is bound raises ValueError."""
        with pytest.raises(ValueError, match="WordSpace .* is not occupied"):
            horizontal_word_space.char_at(1, 2)

    def test_reset_failed_words(self, horizontal_word_space):
        """Test resetting failed words list."""
        horizontal_word_space.failed_words_index_list = [1, 2, 3]

        horizontal_word_space.reset_failed_words()

        assert horizontal_word_space.failed_words_index_list == []

    def test_build_possibility_matrix(self, horizontal_word_space, word_list):
        """Test building possibility matrix."""
        # Add mock crosses
        mock_cross = Mock()
        mock_cross.bound_value.return_value = None  # Unbound cross
        horizontal_word_space.crosses = [mock_cross]

        # Mock _index_of_cross to return an integer
        with patch.object(horizontal_word_space, '_index_of_cross', return_value=0):
            horizontal_word_space.build_possibility_matrix(word_list)

        assert horizontal_word_space.possibility_matrix is not None
        assert horizontal_word_space.possibility_matrix.shape == (1, len(word_list.alphabet))

    def test_update_possibilities_without_matrix_raises_error(self, horizontal_word_space, word_list):
        """Test updating possibilities without initialized matrix raises ValueError."""
        with pytest.raises(ValueError, match="Possibility matrix not initialized"):
            horizontal_word_space.update_possibilities(word_list)

    def test_solving_priority_no_unbounded_crosses(self, horizontal_word_space):
        """Test solving priority when no unbounded crosses."""
        with patch.object(horizontal_word_space, '_get_unbounded_crosses', return_value=[]):
            priority = horizontal_word_space.solving_priority()
            assert priority == 0

    def test_solving_priority_with_unbounded_crosses(self, horizontal_word_space):
        """Test solving priority with unbounded crosses."""
        with patch.object(horizontal_word_space, '_get_unbounded_crosses', return_value=[Mock()]):
            with patch.object(horizontal_word_space, '_count_candidate_crossings', return_value=[5, 3, 7]):
                priority = horizontal_word_space.solving_priority()
                assert priority == 3

    def test_find_best_option_no_options(self, horizontal_word_space, word_list):
        """Test finding best option when no options available."""
        with patch.object(horizontal_word_space, '_find_best_options', return_value=None):
            result = horizontal_word_space.find_best_option(word_list)
            assert result is None

    def test_find_best_option_with_randomization(self, horizontal_word_space, word_list):
        """Test finding best option with randomization."""
        mock_df = pd.DataFrame({
            'word_split': [Word("abc"), Word("def")],
            'score': [10, 5]
        })

        with patch.object(horizontal_word_space, '_find_best_options', return_value=mock_df):
            with patch('numpy.random.poisson', return_value=1):
                result = horizontal_word_space.find_best_option(word_list, randomize=0.5)
                assert result == Word("def")

    def test_max_possibilities_on_cross(self, horizontal_word_space):
        """Test getting maximum possibilities on cross."""
        # Setup possibility matrix
        horizontal_word_space.possibility_matrix = np.array([[1, 2, 3, 4]])

        mock_cross = Mock()
        horizontal_word_space.crosses = [mock_cross]

        max_poss = horizontal_word_space.max_possibilities_on_cross(mock_cross)
        assert max_poss == 4

    def test_to_json_without_occupied_word(self, horizontal_word_space):
        """Test JSON serialization without occupied word."""
        json_data = horizontal_word_space.to_json()

        expected = {
            'start': (1, 2),
            'length': 3,
            'direction': 'horizontal',
            'occupied_by': None,
            'meaning': None
        }
        assert json_data == expected

    def test_to_json_with_occupied_word(self, horizontal_word_space):
        """Test JSON serialization with occupied word."""
        word = Word("abc")
        word.description = "Test description"
        horizontal_word_space.occupied_by = word

        json_data = horizontal_word_space.to_json(export_occupied_by=True)

        assert json_data['occupied_by'] == word.to_json()
        assert json_data['meaning'] == "Test description"

    def test_id_generation(self, horizontal_word_space, vertical_word_space):
        """Test unique ID generation."""
        h_id = horizontal_word_space.id()
        v_id = vertical_word_space.id()

        assert h_id == "horizontal_1_2_3"
        assert v_id == "vertical_2_1_3"
        assert h_id != v_id

    def test_equality(self):
        """Test WordSpace equality comparison."""
        ws1 = WordSpace((1, 2), 3, Direction.HORIZONTAL)
        ws2 = WordSpace((1, 2), 3, Direction.HORIZONTAL)
        ws3 = WordSpace((1, 2), 3, Direction.VERTICAL)
        ws4 = WordSpace((2, 2), 3, Direction.HORIZONTAL)

        assert ws1 == ws2
        assert ws1 != ws3
        assert ws1 != ws4
        assert ws1 != "not a wordspace"

    def test_str_representation(self, horizontal_word_space):
        """Test string representation."""
        str_repr = str(horizontal_word_space)
        assert "Horizontal WordSpace" in str_repr
        assert "starting at (1, 2)" in str_repr
        assert "length 3" in str_repr

    def test_str_representation_with_word(self, horizontal_word_space):
        """Test string representation with occupied word."""
        word = Word("abc")
        horizontal_word_space.occupied_by = word

        str_repr = str(horizontal_word_space)
        assert "occupied by" in str_repr
        assert "abc" in str_repr

    def test_mask_current_no_crosses(self, horizontal_word_space):
        """Test mask creation with no crosses."""
        mask, chars = horizontal_word_space._mask_current()

        assert mask.mask == [False, False, False]
        assert len(chars) == 0

    def test_mask_current_with_bound_crosses(self, horizontal_word_space):
        """Test mask creation with bound crosses."""
        mock_cross = Mock()
        mock_cross.bound_value.return_value = 'a'
        horizontal_word_space.crosses = [mock_cross]

        with patch.object(horizontal_word_space, '_index_of_cross', return_value=1):
            mask, chars = horizontal_word_space._mask_current()

            assert mask.mask == [False, True, False]
            assert chars == Word(['a'])

    def test_get_unbounded_crosses(self, horizontal_word_space):
        """Test getting unbounded crosses."""
        mock_cross1 = Mock()
        mock_cross1.bound_value.return_value = None
        mock_cross2 = Mock()
        mock_cross2.bound_value.return_value = 'a'

        horizontal_word_space.crosses = [mock_cross1, mock_cross2]

        unbounded = horizontal_word_space._get_unbounded_crosses()
        assert len(unbounded) == 1
        assert unbounded[0] == mock_cross1

    def test_get_half_bound_and_unbound_crosses(self, horizontal_word_space):
        """Test getting half-bound and unbound crosses."""
        mock_cross1 = Mock()
        mock_cross1.is_half_bound_or_unbound.return_value = True
        mock_cross2 = Mock()
        mock_cross2.is_half_bound_or_unbound.return_value = False

        horizontal_word_space.crosses = [mock_cross1, mock_cross2]

        half_bound = horizontal_word_space._get_half_bound_and_unbound_crosses()
        assert len(half_bound) == 1
        assert half_bound[0] == mock_cross1

    def test_find_best_options_integration(self, crossed_word_spaces, word_list):
        """Integration test for find_best_options method."""
        ws1, ws2 = crossed_word_spaces

        # Build possibility matrices
        ws1.build_possibility_matrix(word_list)
        ws2.build_possibility_matrix(word_list)

        # Bind a word to create constraints
        ws1.bind(Word("abc"))

        # Find best options for the other word space
        result = ws2._find_best_options(word_list)

        # Should find at least one option
        assert result is not None
        assert len(result) >= 1
        assert 'score' in result.columns
        assert 'word_split' in result.columns

    @pytest.mark.parametrize("direction,expected_spaces", [
        (Direction.HORIZONTAL, [(0, 0), (1, 0), (2, 0)]),
        (Direction.VERTICAL, [(0, 0), (0, 1), (0, 2)]),
    ])
    def test_spaces_parametrized(self, direction, expected_spaces):
        """Parametrized test for spaces generation."""
        ws = WordSpace((0, 0), 3, direction)
        assert ws.spaces() == expected_spaces

    def test_counter_class_variable(self):
        """Test that counter is a class variable."""
        assert hasattr(WordSpace, 'counter')
        assert WordSpace.counter == 1

    def test_failed_words_index_list_operations(self, horizontal_word_space):
        """Test operations on failed words index list."""
        # Initially empty
        assert horizontal_word_space.failed_words_index_list == []

        # Add some failed indices
        horizontal_word_space.failed_words_index_list = [1, 3, 5]

        # Reset should clear the list
        horizontal_word_space.reset_failed_words()
        assert horizontal_word_space.failed_words_index_list == []
