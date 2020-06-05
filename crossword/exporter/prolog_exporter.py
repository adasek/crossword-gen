from pathlib import Path


class PrologExporter(object):
    def __init__(self, directory_name):
        self.directory_name = Path(directory_name)
        self.files = {
            "words": "words.pl",
            "words_usable": "words_usable.pl",
            "word_masks": "word_masks.csv",
            "word_spaces": "word_spaces.pl",
            "word_space_fills": "word_space_fills.pl",
            "crosses": "crosses.pl"
        }
        for file_key in self.files.keys():
            try:
                self.path(file_key).unlink()
            except FileNotFoundError:
                pass

    def path(self, file_key):
        return Path(self.directory_name, self.files[file_key])

    def export_all(self, words, word_spaces, possible_masks, words_by_masks):
        self.export_words(words)
        self.export_words_usable(words)
        self.export_word_masks(possible_masks, words_by_masks)
        self.export_word_space_names(word_spaces)
        self.export_crosses(word_spaces)
        self.export_word_space_fills(word_spaces)

    def export_words(self, words):
        with open(self.path("words"), "a") as words_prolog:
            for word in words:
                    print(f"word({word.id},\"{word}\").", file=words_prolog)

    def export_words_usable(self, words):
        with open(self.path("words_usable"), "a") as words_usable_prolog:
            for word in words:
                print(f"usable_word({word.id}, {word.use}).", file=words_usable_prolog)

    def export_word_masks(self, possible_masks, words_by_masks):
        with open(self.path("word_masks"), "a") as word_masks_csv:
            for mask in possible_masks:
                for chars in words_by_masks[mask]:
                    # word_space('x...x', ['c','t'],'cukat')
                    for word in words_by_masks[mask][chars]:
                        print(f"{mask},{word.id},{self.chars_to_string(chars)}", file=word_masks_csv)

    def export_word_space_names(self, word_spaces):
        with open(self.path("word_spaces"), "a") as word_space_names:
            for word_space in word_spaces:
                crossings_list = ['']*word_space.length
                for cross in word_space.crosses:
                    crossings_list[word_space.index_of_cross(cross)] = cross.id()
                crossings_string = "\",\"".join(crossings_list)
                print(f"word_space(\"{word_space.id()}\",{word_space.length},[\"{crossings_string}\"]).", file=word_space_names)

    def export_crosses(self, word_spaces):
        crosses_lists = [word_space.crosses for word_space in word_spaces]
        crosses = list(set([item for sublist in crosses_lists for item in sublist]))

        with open(self.path("crosses"), "a") as crosses_fp:
            for cross in crosses:
                #  cross(WS1, MaskWS1, WS2, MaskWS2, CrossId),
                print(f"cross(\"{cross.word_space_horizontal.id()}\",\"{cross.mask_one('horizontal')}\",\"{cross.word_space_vertical.id()}\",\"{cross.mask_one('vertical')}\",\"{cross.id()}\").", file=crosses_fp)

    def export_word_space_fills(self, word_spaces):
        with open(self.path("word_space_fills"), "a") as word_space_fills:
            for word_space in word_spaces:
                cross_conditions = [f"cross(\"{cross.id()}\",{cross.id()})" for cross in word_space.crosses]
                print(f"{word_space.to_prolog()} :- {','.join(cross_conditions)}.", file=word_space_fills)


    def chars_to_string(self, chars):
        return ";".join(chars)
