from .charlist import CharList
from .language import split

class Word(CharList):
    id = 1

    def __init__(self, word_string, description="", language='cs', index=None, score=0):
        if(isinstance(word_string, list)):
            word_as_list = word_string
        else:
            word_as_list = split(word_string.lower(), locale_code=language)
        CharList.__init__(self, word_as_list)
        self.use = 1  # probability it will be used
        self.id = Word.id
        self.description = description
        self.score = 0
        self.index = index
        Word.id += 1
