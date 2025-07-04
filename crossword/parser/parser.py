import csv
import itertools
import re
from pathlib import Path

import pandas as pd

from crossword.objects import Word, WordSpace


class Parser(object):
    def __init__(self, directory):
        self.directory = Path(directory)
        self.words_df = None

    def load_dataframe(self, dataframe_file_path):
        self.words_df = pd.read_pickle(dataframe_file_path, compression='gzip')
        # ?? parse into Words objects ??

        return self.words_df

    def words_by_length(self):
        # Structure words #1: do split by lengths:
        self.words_by_len = {}
        for word in self.words:
            length = word.length
            if length not in self.words_by_len:
                self.words_by_len[length] = []
            self.words_by_len[length].append(word)

        return(self.words_by_len)

    def build_possibility_matrix(self, word_spaces, word_list):
        for ws in word_spaces:
            ws.build_possibility_matrix(word_list)
