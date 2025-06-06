import random
from operator import attrgetter
import time
import pandas as pd
import random
from random import gauss
import math


class Solver(object):
    """
    A backtracking crossword puzzles word filler that uses priority-based
    word space selection and constraint propagation.
    """

    def __init__(self):
        self.max_failed_words = 2000
        self.t0 = None
        self.t1 = None
        self.reset()
        self.randomize = True
        self.assign_first_word = True

    def solve(self, crossword, word_list, max_failed_words=2000, randomize=0.5, assign_first_word=True,
              priority_crossing_aggregate: str = 'min', priority_letter_aggregate: str = 'max',
              priority_unbound: int = 0, priority_reverse: bool = False):
        """
       Fill the crossword grid with know words using backtracking with priority-based selection.

        Args:
            crossword: The crossword puzzle grid
            word_list: List of available words to use
            max_failed_words: Maximum number of failed attempts before giving up
            randomize: Probability of randomizing word space selection (0-1)
            assign_first_word: Whether to assign a random first word
            priority_crossing_aggregate: Aggregation method for crossing priorities ('min', 'max', 'mean')
            priority_letter_aggregate: Aggregation method for letter priorities ('min', 'max', 'mean')
            priority_unbound: Priority weight for unbound spaces
            priority_reverse: Whether to reverse priority order

        Returns:
            List of word spaces if solved, False if no solution found
        """
        self._initialize_solve(crossword, max_failed_words, randomize, assign_first_word)

        # Get initial word spaces and assign first word if requested
        word_spaces = self._get_initial_word_spaces(crossword, word_list)

        # Main solving loop using backtracking
        return self._backtrack_solve(
            word_spaces, word_list, crossword,
            priority_crossing_aggregate, priority_letter_aggregate,
            priority_unbound, priority_reverse
        )

    def _initialize_solve(self, crossword, max_failed_words, randomize, assign_first_word):
        """Initialize solver state for a new solve attempt."""
        self.reset()
        crossword.reset()
        self.assign_first_word = assign_first_word
        self.randomize = randomize
        self.max_failed_words = max_failed_words
        self.t0 = time.time()

        for key in self.counters.keys():
            self.counters[key] = 0

    def _get_initial_word_spaces(self, crossword, word_list):
        """
        Get initial word spaces and optionally assign the first word randomly.

        Returns:
            List of remaining word spaces to fill
        """
        word_spaces = list(crossword.word_spaces)

        if self.assign_first_word and word_spaces:
            # Assign first word space randomly
            ws = random.choice(word_spaces)
            word = ws.find_best_option(word_list)
            if word:
                ws.bind(word)
                word_spaces.remove(ws)

        return word_spaces

    def _backtrack_solve(self, word_spaces, word_list, crossword,
                         priority_crossing_aggregate, priority_letter_aggregate,
                         priority_unbound, priority_reverse):
        """
        Main backtracking algorithm template for solving the crossword.

        This implements a general backtracking search with:
        - Priority-based variable ordering (word space selection)
        - Constraint propagation after each assignment
        - Intelligent backtracking with failed word tracking

        Returns:
            Solution (list of word spaces) if found, False otherwise
        """
        assigned_stack = []  # Stack for backtracking: [(word_space, word), ...]
        current_word_space = None
        best_remaining = len(word_spaces)

        while word_spaces or current_word_space:
            # Check termination conditions
            if len(word_spaces) == 0 and current_word_space is None:
                return self._finalize_solution(crossword, True)

            if self._should_terminate():
                return self._finalize_solution(crossword, False)

            # Select next word space if none is currently being processed
            if current_word_space is None:
                current_word_space = self._select_next_word_space(
                    word_spaces, word_list,
                    priority_crossing_aggregate, priority_letter_aggregate,
                    priority_unbound, priority_reverse
                )

                if current_word_space is None:
                    # No valid word spaces available - backtrack
                    current_word_space = self._backtrack(assigned_stack, word_spaces, word_list)
                    continue

            # Try to assign a word to the current word space
            best_word = current_word_space.find_best_option(word_list)

            if best_word is None:
                # No valid word found - backtrack
                current_word_space = self._backtrack(assigned_stack, word_spaces, word_list)
            else:
                # Assign word and propagate constraints
                current_word_space = self._assign_word(
                    current_word_space, best_word, assigned_stack,
                    word_spaces, word_list, best_remaining
                )
                best_remaining = min(best_remaining, len(word_spaces))

        return self._finalize_solution(crossword, True)

    def _select_next_word_space(self, word_spaces, word_list,
                                priority_crossing_aggregate, priority_letter_aggregate,
                                priority_unbound, priority_reverse):
        """
        Select the next word space to fill based on priority heuristics.

        Uses constraint satisfaction heuristics like most-constrained-variable
        and most-constraining-variable to guide the search.

        Returns:
            Selected WordSpace object or None if no valid spaces
        """
        if not word_spaces:
            return None

        # Sort word spaces by solving priority
        sorted_spaces = sorted(
            word_spaces,
            key=lambda ws: ws.solving_priority(
                word_list=word_list,
                crossing_aggregate=priority_crossing_aggregate,
                letter_aggregate=priority_letter_aggregate,
                unbound=priority_unbound
            ),
            reverse=priority_reverse
        )

        # Apply randomization if enabled
        if (self.randomize > 0 and random.random() < self.randomize
                and len(sorted_spaces) > 1):
            # Swap first two elements to add some randomness
            sorted_spaces[0], sorted_spaces[1] = sorted_spaces[1], sorted_spaces[0]

        selected_space = sorted_spaces[0]
        selected_space.failed_words_index_set = set()
        return selected_space

    def _assign_word(self, word_space, word, assigned_stack, word_spaces, word_list, best_remaining):
        """
        Assign a word to a word space and propagate constraints.

        Args:
            word_space: The word space to assign to
            word: The word to assign
            assigned_stack: Stack of assignments for backtracking
            word_spaces: List of remaining word spaces
            word_list: Available words
            best_remaining: Best remaining count so far

        Returns:
            None (indicating to select next word space)
        """
        # Bind word to space and get affected spaces
        affected_spaces = word_space.bind(word)

        # Propagate constraints to affected spaces
        for affected_space in affected_spaces:
            affected_space.rebuild_possibility_matrix(word_list)

        # Update tracking
        assigned_stack.append((word_space, word))
        word_spaces.remove(word_space)
        self.counters['assign'] += 1

        # Progress reporting
        if self.counters['assign'] % 100 == 0:
            self._report_progress(len(word_spaces), best_remaining)

        return None  # Signal to select next word space

    def _backtrack(self, assigned_stack, word_spaces, word_list):
        """
        Perform backtracking when no valid assignment is found.

        Args:
            assigned_stack: Stack of previous assignments
            word_spaces: List of remaining word spaces
            word_list: Available words

        Returns:
            WordSpace to retry or None if backtracking failed
        """
        self.counters['backtrack'] += 1

        if not assigned_stack:
            # No more assignments to backtrack - puzzle is unsolvable
            return None

        # Pop the most recent assignment
        failed_word_space, failed_word = assigned_stack.pop()

        # Unbind the word and get affected spaces
        affected_spaces = failed_word_space.unbind()

        # Rebuild possibility matrices for affected spaces
        failed_word_space.rebuild_possibility_matrix(word_list)

        # Add the failed word space back to the list
        word_spaces.append(failed_word_space)

        # Mark this word as failed for this space
        failed_word_space.failed_words_index_set.add(failed_word.index)

        self.counters['failed'] += 1

        return failed_word_space

    def _should_terminate(self):
        """Check if solving should be terminated due to too many failures."""
        return self.counters['failed'] > self.max_failed_words

    def _finalize_solution(self, crossword, solution_found):
        """
        Finalize the solving process and return results.

        Args:
            crossword: The crossword object
            solution_found: Whether a solution was found

        Returns:
            Solution or False
        """
        self.t1 = time.time()
        self.solved = True
        self.solution_found = solution_found

        if solution_found:
            self.score = crossword.evaluate_score()
            self.solution = crossword.word_spaces
            return crossword.word_spaces
        else:
            return False

    def _report_progress(self, remaining_spaces, best_remaining):
        """Report solving progress."""
        print(f"Assigned {self.counters['assign']}, remaining: {remaining_spaces}/{best_remaining}")

    def time_elapsed(self):
        """
        Get the time elapsed during solving.

        Returns:
            Float: Time in seconds

        Raises:
            Exception: If called before solve() completes
        """
        if not self.solved:
            raise Exception("Not solved")
        return self.t1 - self.t0

    def reset(self):
        """Reset solver state for a new solving attempt."""
        self.score = 0
        self.solved = False
        self.solution_found = False
        self.solution = None
        self.counters = {'assign': 0, 'backtrack': 0, 'failed': 0}