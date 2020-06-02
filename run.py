#!/usr/bin/env python3
from crossword.parser import Parser
from crossword.exporter import PrologExporter
from crossword.solver import Solver

# For found mask, e.g. X..XX generate all its children:
# {...XX,X...X,X..X.,....X,X....,...X.}
# Maximal length of mask to have all its children generated ( 2^x masks)!
# Zero means no children masks would be generated
MASK_LENGTH_TRESHOLD = 16

parser = Parser(".")
words, words_by_length = parser.parse_words("wordlist.dat")
crossword = parser.parse_crossword("crossword.dat")
word_spaces = parser.parse_word_spaces(crossword)
parser.add_crosses(word_spaces)

possible_masks = parser.create_possible_masks(word_spaces, MASK_LENGTH_TRESHOLD)
print(len(possible_masks))
words_by_masks = parser.create_words_by_masks(words, possible_masks)

exporter = PrologExporter("prolog_output")
exporter.export_all(words, word_spaces, possible_masks, words_by_masks)

# Solve
solver = Solver(MASK_LENGTH_TRESHOLD)
solver.solve(word_spaces, words_by_length, words_by_masks)