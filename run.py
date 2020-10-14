#!/usr/bin/env python3
from crossword.exporter import PrologExporter
from crossword.runner import Runner
from crossword.objects import WordList
from crossword.parser import Parser
from crossword.solver import Solver
from crossword.objects import Crossword
from pathlib import Path
import json
import cProfile

DIRECTORY = "."
parser = Parser(DIRECTORY)

#dict_file = "input/Czech.dic"
#words = parser.parse_original_wordlist(dict_file)

words = parser.parse_csv_wordlist("../word-gen/meanings_filtered.txt", delimiter=':')
words_by_length = parser.words_by_length()
crossword = Crossword.from_grid(Path(DIRECTORY, "crossword.dat"))


word_list = WordList(words, crossword.word_spaces)
parser.build_possibility_matrix(crossword.word_spaces, word_list)

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

#exporter = PrologExporter("dataset")
#exporter.export_all(words, word_spaces, possible_masks, words_by_masks)


#runner = Runner('../solve.pl', "dataset")
#runner.run()
#runner.fetch_results(word_spaces)
#print(runner.output(), flush=True)

# Solve
print("Solving:")
solver = Solver()
original_word_spaces = crossword.word_spaces
#cProfile.run('word_spaces = solver.solve(word_spaces, word_list, crossword)', 'restats')
word_spaces = solver.solve(crossword, word_list)
if not word_spaces:
    print(crossword)
    print(f"No solutions found")
else:
    print(crossword)
    with open('out_crossword.json', 'w') as json_out:
        json_out.write(json.dumps(json.loads(crossword.to_json()), sort_keys=True, indent=4))
