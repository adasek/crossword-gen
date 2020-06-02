from crossword.parser import Parser
from crossword.exporter import PrologExporter
import os
import time
import subprocess

# Experiment 1:
# generate_8grid ~ words of length=8
class Experiment1:
  def __init__(self, dictionary_filename):

    parser = Parser(".")

    # modify wordlist so that it contains only words of 8
    words_all = parser.parse_original_wordlist(dictionary_filename)
    words = [word for word in words_all if word.length == 8]
    parser.words = words
    words_by_length = parser.words_by_length()

    for number_of_words in range(8, 400):
      with open('experiment/1-crossword.dat', 'w') as crossword_fp:
        for line_number in range(0, number_of_words):
          print("X"*line_number, sep="", end="", file=crossword_fp)
          print("_"*8, sep="", end="", file=crossword_fp)
          print("X"*(number_of_words - line_number), sep="", end="\n", file=crossword_fp)

      # Run
      crossword = parser.parse_crossword("experiment/1-crossword.dat")

      word_spaces = parser.parse_word_spaces(crossword)

      # Filter out only 8 word spaces
      word_spaces = [w for w in word_spaces if w.length == 8]

      parser.add_crosses(word_spaces)

      possible_masks = parser.create_possible_masks(word_spaces)
      words_by_masks = parser.create_words_by_masks(words, possible_masks)

      exporter = PrologExporter("experiment")
      exporter.export_all(words, word_spaces, possible_masks, words_by_masks)

      t0 = time.time()
      process = subprocess.run(['prolog', '../solve.pl'], cwd='experiment', capture_output=True)
      output = process.stdout
      # Parse output: first two lines contain load_time and compute_time
      # other lines contains values of WordSpaces
      compute_time = 0
      load_time = 0
      try:
        output_dict = {line.split(":")[0]: line.split(":")[1] for line in output.decode('utf-8').split("\n") if line.strip() != ''}
        compute_time = output_dict['compute_time']
        load_time = output_dict['load_time']
      except (IndexError, KeyError):
        print("--------")
        print(output.decode('utf-8'))
        print("--------")
        raise Exception("Unexpected prolog program output format")

      t1 = time.time()

      print(f"{number_of_words},{t1-t0},{load_time},{compute_time},{process.returncode}", flush=True)

