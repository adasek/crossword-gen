from pathlib import Path
from crossword.objects import Word, WordSpace
import re
import itertools
import csv

class Parser(object):
    def __init__(self, directory):
        self.directory = Path(directory)
        self.words = []
        self.words_by_len = {}

    def parse_original_wordlist(self, original_wordlist_file):
        with open(original_wordlist_file) as fp:
            lines = fp.readlines()

            self.words = [Word(line.split('/')[0].lower().strip()) for line in lines]
        return self.words

    def parse_csv_wordlist(self, wordlist_file, delimiter=','):
        with open(wordlist_file) as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=delimiter)
            self.words = []
            for row in csv_reader:
                self.words.append(Word(row[0].lower().strip(), description=row[1].strip()))
        return self.words

    def parse_words(self):
        # Load words
        self.words = []
        with open(Path(self.directory, wordlist_file), 'r') as fp:
            for word_string in fp.readlines():
                self.words.append(Word(re.sub(r'[\r\n\t]*', '', word_string)))

        return self.words

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

    def create_possible_masks(self, word_spaces, generate_children_threshold=0, generate_prefix=False):
        possible_masks = set()
        for word_space in word_spaces:
            if word_space.mask() not in possible_masks:
                if generate_children_threshold > 0:
                    possible_masks.update(word_space.masks_all(generate_children_threshold))
                if generate_prefix:
                    possible_masks.update(word_space.masks_prefix())

                possible_masks.add(word_space.mask())


        return possible_masks
