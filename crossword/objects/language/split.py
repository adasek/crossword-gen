from . import alphabet
from typing import Union, List


def split(word: str, locale_code: str) -> Union[List[str], bool]:
    """
    Split one word according to locale alphabet

    Args:
        word: string to split
        locale_code: ISO 639-1 language specification (e.g. 'en', 'cs')

    Returns:
        List of locale own language atoms (characters) or False if unknown letter encoutered
    """
    word_characters = []
    while len(word) > 0:
        found_match = False
        for alphabet_char in sorted(alphabet(locale_code), key=len, reverse=True):
            if word.startswith(alphabet_char):
                word_characters.append(alphabet_char)
                word = word[len(alphabet_char):]
                found_match = True
                break
        if not found_match:
            return False
    return word_characters
