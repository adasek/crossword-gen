from .charlist import CharList

class Word(CharList):
    id = 1

    def __init__(self, word_string, description=""):
        word_as_list = list(word_string)
        CharList.__init__(self, word_as_list)
        self.use = 1  # probability it will be used
        self.id = Word.id
        self.description = description
        Word.id += 1
