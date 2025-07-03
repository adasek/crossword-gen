import random
import time

import numpy as np

from crossword.objects import WordList, WordSpace


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
        self.randomize = 1.0

    def solve(self, crossword, word_list, max_failed_words=2000, randomize=0.5):
        """
       Fill the crossword grid with know words using backtracking with priority-based selection.

        Args:
            crossword: The crossword puzzle grid
            word_list: List of available words to use
            max_failed_words: Maximum number of failed attempts before giving up
            randomize: Probability of randomizing word space selection (0-1)

        Returns:
            List of word spaces if solved, False if no solution found
        """
        self._initialize_solve(crossword, max_failed_words, randomize)

        # Get initial word spaces and assign first word if requested
        word_spaces = self._get_initial_word_spaces(crossword, word_list)

        # Main solving loop using backtracking
        return self._backtrack_solve(
            word_spaces, word_list, crossword
        )

    def _initialize_solve(self, crossword, max_failed_words, randomize):
        """Initialize solver state for a new solve attempt."""
        self.reset()
        crossword.reset()
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

        # Assign first word space randomly
        if self.randomize > 0:
            ws = random.choice(word_spaces)
        else:
            ws = word_spaces[0]
        word = ws.find_best_option(word_list, randomize=self.randomize)
        if word:
            affected_spaces = ws.bind(word)
            word_spaces.remove(ws)
            self._update_possibilities_affected(affected_spaces, word_list)

        return word_spaces

    def _backtrack_solve(self, word_spaces, word_list, crossword):
        """
        Main backtracking algorithm template for solving the crossword.

        This implements intelligent backtracking search with:
        - Priority-based variable ordering (word space selection)
        - Constraint propagation after each assignment
        - Multi-step backtracking to escape unpromising branches
        - Branch jumping to avoid getting stuck in bad search paths

        Returns:
            Solution (list of word spaces) if found, False otherwise
        """

        assigned_stack = []  # Stack for backtracking: [(word_space, word), ...]
        current_word_space = None
        best_remaining = len(word_spaces)
        consecutive_backtracks = 0  # Track consecutive backtracking to detect stuck situations

        while word_spaces or current_word_space:
            if self._should_terminate():
                return self._finalize_solution(crossword, False)

            # Select next word space if none is currently being processed
            if current_word_space is None:
                current_word_space = self._select_next_word_space(word_spaces, word_list)

                if current_word_space is None:
                    # No valid word spaces available - backtrack (potentially multiple steps)
                    current_word_space = self._backtrack(assigned_stack, word_spaces, word_list)
                    consecutive_backtracks += 1
                    continue

            # Try to assign a word to the current word space
            best_word = current_word_space.find_best_option(word_list)

            if best_word is None:
                # No valid word found - backtrack (potentially multiple steps)
                current_word_space = self._backtrack(assigned_stack, word_spaces, word_list)
                consecutive_backtracks += 1

                # If we're backtracking too much, try more aggressive multi-step backtracking
                if consecutive_backtracks > 10:
                    current_word_space = self._backtrack(assigned_stack, word_spaces, word_list,
                                                         max_backtrack_steps=min(5, len(assigned_stack)))
                    consecutive_backtracks = 0  # Reset counter after aggressive backtrack
            else:
                # Assign word and propagate constraints
                current_word_space = self._assign_word(
                    current_word_space, best_word, assigned_stack,
                    word_spaces, word_list, best_remaining
                )
                best_remaining = min(best_remaining, len(word_spaces))
                consecutive_backtracks = 0  # Reset counter on successful assignment

        return self._finalize_solution(crossword, True)

    def _select_next_word_space(self, word_spaces: list[WordSpace], word_list: WordList):
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
            key=lambda ws: ws.solving_priority(),
            reverse=False
        )

        choice_index = 0
        # Apply randomization if enabled
        if self.randomize > 0 and random.random() < self.randomize:
            choice_index = np.random.poisson(lam=2)
            if choice_index > len(sorted_spaces) - 1:
                choice_index = random.randint(0, len(sorted_spaces) - 1)

        selected_space = sorted_spaces[choice_index]
        # todo: accessor
        selected_space.failed_words_index_list = []
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
        self._update_possibilities_affected(affected_spaces, word_list)

        # Update tracking
        assigned_stack.append((word_space, word))
        word_spaces.remove(word_space)
        self.counters['assign'] += 1

        # Progress reporting
        if self.counters['assign'] % 100 == 0:
            self._report_progress(len(word_spaces), best_remaining)

        return None  # Signal to select next word space

    def _update_possibilities_affected(self, affected_word_spaces: list[WordSpace], word_list: WordList):
        # Propagate constraints to affected spaces
        for affected_space in affected_word_spaces:
            affected_space.update_possibilities(word_list)

    def _backtrack(self, assigned_stack, word_spaces, word_list, max_backtrack_steps=5):
        """
        Perform intelligent backtracking when no valid assignment is found.

        This method can backtrack multiple steps to escape unpromising branches:
        - Single step: Normal backtracking
        - Multiple steps: When we detect we're in a bad branch (consecutive failures)
        - Branch jumping: Skip back to a more promising point in the search tree

        Args:
            assigned_stack: Stack of previous assignments
            word_spaces: List of remaining word spaces
            word_list: Available words
            max_backtrack_steps: Maximum number of steps to backtrack in one go

        Returns:
            WordSpace to retry or None if backtracking failed
        """
        self.counters['backtrack'] += 1

        if not assigned_stack:
            # No more assignments to backtrack - puzzle is unsolvable
            return None

        # Determine how many steps to backtrack based on failure patterns
        steps_to_backtrack = self._calculate_backtrack_steps(assigned_stack, max_backtrack_steps)

        backtracked_spaces = []
        last_space = None

        # Perform multi-step backtracking
        for step in range(steps_to_backtrack):
            if not assigned_stack:
                break

            # Pop assignment
            failed_word_space, failed_word = assigned_stack.pop()

            # Unbind the word and get affected spaces
            affected_spaces = failed_word_space.unbind()

            # Mark this word as failed for this space
            failed_word_space.failed_words_index_list.append(failed_word.index)

            self._update_possibilities_affected([failed_word_space] + affected_spaces, word_list)

            # Add the failed word space back to the list
            word_spaces.append(failed_word_space)
            backtracked_spaces.append(failed_word_space)

            self.counters['failed'] += 1

        # Return the earliest backtracked space to retry
        # This gives us a better chance of finding alternative paths
        return backtracked_spaces[-1] if backtracked_spaces else None

    def _calculate_backtrack_steps(self, assigned_stack, max_steps):
        """
        Calculate how many steps to backtrack based on failure patterns.

        Strategies for detecting unpromising branches:
        1. Consecutive failures: If recent assignments keep failing
        2. Low possibility count: If current branch has very few options
        3. Deep search: If we've gone deep without progress

        Args:
            assigned_stack: Current assignment stack
            max_steps: Maximum allowed backtrack steps

        Returns:
            Number of steps to backtrack (1 to max_steps)
        """
        if len(assigned_stack) < 2:
            return 1

        # Strategy 1: Check for consecutive failures
        consecutive_failures = self._count_consecutive_failures()

        # Strategy 2: Check depth vs progress ratio
        current_depth = len(assigned_stack)
        failure_rate = self.counters['failed'] / max(1, self.counters['assign'])

        # Strategy 3: Check if recent assignments have very few alternatives
        recent_low_options = self._count_recent_low_option_assignments(assigned_stack)

        # Determine backtrack steps based on heuristics
        steps = 1  # Default single step

        # Increase steps based on failure patterns
        if consecutive_failures >= 3:
            steps = min(3, max_steps)
        elif failure_rate > 0.3 and current_depth > 10:
            steps = min(2, max_steps)
        elif recent_low_options >= 2:
            steps = min(2, max_steps)

        # Adaptive: backtrack more aggressively as failures increase
        if self.counters['failed'] > 100:
            steps = min(steps + 1, max_steps)

        return min(steps, len(assigned_stack), max_steps)

    def _count_consecutive_failures(self):
        """
        Count recent consecutive backtracking events.
        This helps detect when we're stuck in a bad branch.
        """
        # This is a simplified version - in practice you might want to
        # track failure history more sophisticated
        return min(self.counters['backtrack'] % 10, 5)

    def _count_recent_low_option_assignments(self, assigned_stack, lookback=3):
        """
        Count how many recent assignments were made to word spaces with very few options.
        This indicates we might be in an over-constrained branch.

        Args:
            assigned_stack: Current assignments
            lookback: How many recent assignments to check

        Returns:
            Count of recent low-option assignments
        """
        if len(assigned_stack) < lookback:
            return 0

        low_option_count = 0
        # Check the last few assignments
        for i in range(min(lookback, len(assigned_stack))):
            word_space, word = assigned_stack[-(i + 1)]
            # Heuristic: if a word space had very few failed words,
            # it probably had few options when we assigned to it
            if len(word_space.failed_words_index_list) <= 2:
                low_option_count += 1

        return low_option_count

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
        # print(f"Assigned {self.counters['assign']}, remaining: {remaining_spaces}/{best_remaining}")

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
