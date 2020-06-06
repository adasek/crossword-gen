#!/usr/bin/env python3
from crossword.exporter import PrologExporter
from crossword.runner import Runner
from crossword.objects import WordList
from crossword.parser import Parser
from crossword.solver import Solver
import cProfile

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

# (start with 1-masks)
# X..X.,'ab' = X....,'a' union ...X.,'b'
#  WordList[mask][chars]

# WordSpaces x Words precomputation:
# for every WordSpace produces matrix
# wordlen x number_of_words
# this matrix is in WordSpace and is immutable

# Algorithm:
# word_spaces_to_fill_next = sorted(word_spaces, key=lambda ws: ws.expectation_value(words_by_masks), reverse=True)
# Exceptation value is maximum from  WSMatrix*(inverted_bind_vector)
#
# [20 50 10]
# [5 0 10]
# inverted_bind_vector = [true, false]^-1
#
# max[inverted_bind_vector] se cachuje
word_list = WordList(words, word_spaces)

#exporter = PrologExporter("dataset")
#exporter.export_all(words, word_spaces, possible_masks, words_by_masks)


#runner = Runner('../solve.pl', "dataset")
#runner.run()
#runner.fetch_results(word_spaces)
#print(runner.output(), flush=True)

# Solve
print("Solving:")
solver = Solver(MASK_LENGTH_TRESHOLD)
#cProfile.run('word_spaces = solver.solve(word_spaces, word_list)', 'restats')
word_spaces = solver.solve(word_spaces, word_list)
solver.print(word_spaces, crossword)