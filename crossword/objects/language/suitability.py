from .alphabet import alphabet_multiletters_from_singleletters, alphabet_set
from .split import split


def is_crossword_suitable(word: str, locale_code: str, max_length: int = 20) -> bool:
    """
    Determine if a word is usable in a crossword - contains only allowed letters and does not exceed max_length

    Args:
        word: string to analyze
        locale_code: ISO 639-1 language specification (e.g. 'en', 'cs')
        max_length: maximal number of atoms acceptable in the word

    Returns:
        if the word can be used in a crossword
    """
    alphabet_set_possible_characters = alphabet_set(locale_code, only_characters=True)
    word_lower = word.lower()
    for char in word_lower:
        if char not in alphabet_set_possible_characters:
            return False

    # fast track: if word is short enough when we count multiletter ExemplarSet as 2
    # it would be short enough when we don't
    if alphabet_multiletters_from_singleletters(locale_code) and 0 < len(word_lower) <= max_length:
        return True

    # Do the proper word split in the locale
    word_characters = split(word_lower, locale_code)
    if not word_characters:
        return False
    return 0 < len(word_characters) <= max_length
