from crossword.exporter import PrologExporter
from crossword.objects import WordList
from crossword.parser import Parser
from crossword.solver import Solver


# Experiment 2:
# generate_8grid ~ words of length=8
# and solve with python
class Experiment2:
  def __init__(self, dictionary_filename):

    parser = Parser(".")

    # modify wordlist so that it contains only words of 4
    words_all = parser.parse_original_wordlist(dictionary_filename)
    words = [word for word in words_all if word.length == 4]
    parser.words = words

    for number_of_words in range(4, 100):
      with open('experiment/1-crossword.dat', 'w') as crossword_fp:
        for line_number in range(0, number_of_words):
          print("X"*line_number, sep="", end="", file=crossword_fp)
          print("_"*4, sep="", end="", file=crossword_fp)
          print("X"*(number_of_words - line_number), sep="", end="\n", file=crossword_fp)

      # Run
      crossword = parser.parse_crossword("experiment/1-crossword.dat")

      word_spaces = parser.parse_word_spaces(crossword)

      # Filter out only n- word spaces
      word_spaces = [w for w in word_spaces if w.length == 4]

      parser.add_crosses(word_spaces)
      word_list = WordList(words, word_spaces)
      parser.build_possibility_matrix(word_spaces, word_list)

      solver = Solver()
      word_spaces = solver.solve(word_spaces, word_list, crossword)
      print(f"{number_of_words},{solver.solution_found},{solver.time_elapsed()},{solver.counters['assign']},{solver.counters['backtrack']}")
      #if solver.solution_found:
      #  solver.print(word_spaces, crossword)
