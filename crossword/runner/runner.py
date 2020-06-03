import os
import time
import subprocess
from crossword.objects import Word


class Runner(object):
    def __init__(self, prolog_program, cwd):
        self.prolog_program = prolog_program
        self.cwd = cwd
        self.t0 = None
        self.t1 = None
        self.return_code = 0
        self.output_dict = {}

    def run(self):
        self.t0 = time.time()
        process = subprocess.run(['prolog', self.prolog_program], cwd=self.cwd, capture_output=True)
        output = process.stdout
        self.return_code = process.returncode
        # Parse output: first two lines contain load_time and compute_time
        # other lines contains values of WordSpaces
        compute_time = 0
        load_time = 0
        try:
            self.output_dict = {line.split(":")[0]: line.split(":")[1] for line in output.decode('utf-8').split("\n") if
                           line.strip() != ''}
            self.output_dict['compute_time']
            self.output_dict['load_time']
        except (IndexError, KeyError):
            print("--------")
            print(output.decode('utf-8'))
            print("--------")
            raise Exception("Unexpected prolog program output format")

        self.t1 = time.time()

    def output(self):
        return f"{self.t1 - self.t0},{self.output_dict['load_time']},{self.output_dict['compute_time']},{self.return_code}"

    def fetch_results(self, word_spaces):
        print(self.output_dict)
        for word_space in word_spaces:
            word_string = self.output_dict[f"\"{word_space.id()}\""].strip("\" ")
            word_space.bind(Word(word_string))

        for word_space in word_spaces:
            if not word_space.check_crosses():
                raise Exception("Cross check failed")
