from .charlist import CharList


class WordCombinator:
    def __init(self, word_space):
        self.word_space = word_space
        self.counts = []
        self.active_chars = []
        self.iterators = []

    def update(self, word_list):
        unbounded_crosses = self.word_space.get_unbounded_crosses()
        self.counts = []
        for cross_index, cross in enumerate(unbounded_crosses):
            other_wordspace = cross.other(self)
            # Dict Char=>Int
            char_counts = other_wordspace.get_counts(word_list)
            self.counts[cross_index] = sorted(char_counts, key=char_counts.get, reverse=True)

        def __iter__(self):
            self.active_chars = [' '] * len(self.counts)
            self.iterators = [] * len(self.counts)
            for i, char_count in enumerate(self.counts):
                self.iterators[i] = iter(char_count)
                self.active_chars[i] = next(self.iterators[i])
            return self

        def __next__(self):
            result = [ch for ch in self.actual_chars]
            # move iterator:
            # determine where to iterate next
            min(next_chars)
            if self._iter_counter < self.length:
                result = self.char_list[self._iter_counter]
                self._iter_counter += 1
                return result
            return result
            #    raise StopIteration


            my_iterator = iter(favorite_numbers)
            next(my_iterator)

            other_wordspace_mask, other_wordspace_chars = other_wordspace.mask_current()
            original_wordspace_index = self.index_of_cross(cross)
            other_wordspace_index = other_wordspace.index_of_cross(cross)
            base_set = word_list.words(other_wordspace_mask, other_wordspace_chars)
            mask_list = [False] * other_wordspace.length
            mask_list[other_wordspace_index] = True
            one_mask = Mask(mask_list)

            candidate_chars = []
            for char in word_list.alphabet:
                words_count = len(base_set.intersection(word_list.words(one_mask, CharList([char]))))
                if words_count > 0:
                    candidate_chars.append({'char': char, 'count': words_count})
            if len(candidate_chars) == 0:
                return None
            sorted_candidate_char_records = sorted(candidate_chars, key=lambda rec: rec['count'], reverse=True)
            candidate_chars_array.append(sorted_candidate_char_records)
            candidate_char_dict_array.append({obj['char']:obj['count'] for obj in sorted_candidate_char_records})
            char_list_array.append(list(map(lambda rec: rec['char'], sorted_candidate_char_records)))
