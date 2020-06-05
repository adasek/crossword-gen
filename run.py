#!/usr/bin/env python3
from crossword.parser import Parser
from crossword.exporter import PrologExporter
from crossword.runner import Runner
from crossword.solver import Solver

# For found mask, e.g. X..XX generate all its children:
# {...XX,X...X,X..X.,....X,X....,...X.}
# Maximal length of maparse_original_wordlistsk to have all its children generated ( 2^x masks)!
# Zero means no children masks would be generated
MASK_LENGTH_TRESHOLD = 9

parser = Parser(".")

#dict_file = "input/Czech.dic"
dict_file = "input/altered.dic"
words = parser.parse_original_wordlist(dict_file)
words_by_length = parser.words_by_length()
crossword = parser.parse_crossword("crossword.dat")
word_spaces = parser.parse_word_spaces(crossword)

parser.add_crosses(word_spaces)

possible_masks = parser.create_possible_masks(word_spaces, MASK_LENGTH_TRESHOLD, True)
words_by_masks = parser.create_words_by_masks(words, possible_masks)

exporter = PrologExporter("dataset")
exporter.export_all(words, word_spaces, possible_masks, words_by_masks)


runner = Runner('../solve.pl', "dataset")
runner.run()
runner.fetch_results(word_spaces)
print(runner.output(), flush=True)

# Solve
#solver = Solver(MASK_LENGTH_TRESHOLD)
#solver.solve(word_spaces, words_by_length, words_by_masks)
