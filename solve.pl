:- initialization mark_start_time, load_words, load_words_usable, load_word_spaces  , load_word_masks, load_crosses, generate_cross.

:- set_prolog_flag(double_quotes, atom).
:- use_module(library(clpr/bv_r)).

mark_start_time :-
 get_time(TimeStarted),
 assertz(get_time_started(TimeStarted)).

load_words_usable :-
 consult(words_usable).

load_words :-
 consult(words).

load_word_spaces :-
 consult(word_spaces).


load_word_masks :-
 read_file_to_string("../dataset/word_masks.csv", DataFileString, []),
 split_string(DataFileString, "\n", "", Lines),
 maplist(parse_word_mask_line, Lines).

parse_word_mask_line(Str) :-
 string_length(Str,Len),
 =(Len, 0).

parse_word_mask_line(Line) :-
 split_string(Line, ",", "", List),
 assert_wordmask(List).

assert_wordmask(List) :-
  nth1(1, List, Mask),
  nth1(2, List, WordIdStr),
  nth1(3, List, CharString),
  atom_number(WordIdStr, WordIdInt),
      split_string(CharString, ";", "", CharList),
  chars_to_mask_fill(CharList, Hash),
  assertz(word_mask(Mask, WordIdInt, Hash)).

load_crosses :-
 consult(crosses).

%%%%%
chars_to_mask_fill(Chars, String) :-
   atomics_to_string(Chars,";", String).
   %crypto_data_hash(String, Hash, [algorithm(md5)]).

%%%%%
bind_cross(DataIn, CrossId, Char, DataOutter) :-
 cross(WS1, MaskWS1, WS2, MaskWS2, CrossId),
 alphabet(Alphabet),
 member(CharAtom, Alphabet),
 atom_string(CharAtom,Char),
 %print(Char),print("A"),nl,
 word_exists(DataIn, MaskWS1, Char, WS1, _,  DataOut),
 word_exists(DataOut, MaskWS2, Char, WS2, _, DataOutter).

word_exists(DataIn, Mask, Char, WordSpaceId, NumWords, DataOut) :-
 find_mask(DataIn, WordSpaceId, OldMask, OldChars),
 combine_masks(Mask, [Char], OldMask, OldChars, NewMask, NewChars),
 %print("word_exists"),write(NewMask),print(":"),print(NewChars),nl,
 %word_mask(NewMask, WordId, NewChars),
 chars_to_mask_fill(NewChars, MaskFill),
 findall(WordId, word_mask(NewMask, WordId, MaskFill), WordIds),
 length(WordIds, NumWords),
 %print(NumWords),nl,
 >(NumWords, 0),
 update_mask(DataIn, WordSpaceId, NewMask, NewChars, DataOut).

find_mask(Data, WordSpaceId, Mask, Chars) :-
    get_dict(WordSpaceId, Data, Record),
    get_dict(mask, Record, Mask),
    get_dict(chars, Record, Chars).

combine_masks(Mask1, Chars1, Mask2, Chars2, NewMask, NewChars) :-
    string_chars(Mask1, Mask1List),
    string_chars(Mask2, Mask2List),
    combine_mask_lists(Mask1List, Chars1, Mask2List, Chars2, NewMaskList, NewChars),
    atomics_to_string(NewMaskList, NewMask).

combine_mask_lists([], [], [], [], [], []).

combine_mask_lists(["X"|Mask1List], [C|Chars1], ["."|Mask2List], Chars2, ["X"|NewMaskList], [C|NewChars]) :-
    combine_mask_lists(Mask1List, Chars1, Mask2List, Chars2, NewMaskList, NewChars).

combine_mask_lists(["."|Mask1List], Chars1, ["X"|Mask2List], [C|Chars2], ["X"|NewMaskList], [C|NewChars]) :-
    combine_mask_lists(Mask1List, Chars1, Mask2List, Chars2, NewMaskList, NewChars).

combine_mask_lists(["."|Mask1List], Chars1, ["."|Mask2List], Chars2, ["."|NewMaskList], NewChars) :-
    combine_mask_lists(Mask1List, Chars1, Mask2List, Chars2, NewMaskList, NewChars).


update_mask(DataIn, WordSpaceId, NewMask, NewChars, DataOut) :-
    %write("update_mask WordSpaceId="),print(WordSpaceId),nl,
    %write("update_mask NewMask="),print(NewMask),nl,
    put_dict(WordSpaceId, DataIn, _{mask: NewMask, chars: NewChars} , DataOut).



%%%%%%%%%%%

%! find_and_output_word_space(+WordSpaceName:string, -WordId:integer) is nondet
%% For a WordSpace find a suitable Word and return its id.
find_word_space(WordSpaceName, WordId) :-
    word_space_fill(Mask, Chars, WordSpaceName),
    word_mask(Mask, WordId, Chars),
    usable_word(WordId, 1).

% https://stackoverflow.com/a/15865303
not_in_used_words(_, []).

not_in_used_words(X, [WordId|Tail]) :-
     X \= WordId,
    not_in_used_words(X, Tail).

%! solve_crosses(+CrossNames:list, +UsedWordsBefore:list, -UsedWords:list) is nondet
%% Recursively call search for suitable word for every WordSpace given in first parameter
%% After match is made, remove the word from usable words
solve_crosses(Data,[],Data).
solve_crosses(DataIn, [CrossId | Rest],  DataBack) :-
    %write("solve_crosses0:"),print(CrossId),nl,
    %write(DataIn),nl,
    bind_cross(DataIn, CrossId, _,  DataOut),
    solve_crosses(DataOut, Rest,  DataBack).


initialize_word_masks(OutDict, [], OutDict).
initialize_word_masks(InDict, [WordSpaceId|WordSpaceList], OutDict) :-
 word_space(WordSpaceId, WordLength, _),
 empty_mask(WordLength, Mask),
 put_dict(WordSpaceId, InDict, _{mask: Mask, chars: []}, Dict),
 initialize_word_masks(Dict, WordSpaceList, OutDict).

empty_mask(Length, "") :- =(Length, 0).
empty_mask(Length, OutStr) :-
LenDec is Length - 1,
>(Length, 0),
empty_mask(LenDec, InStr),
string_concat(".", InStr, OutStr).

%! print_word_spaces(+WordSpaceNames:list, +UsedWords:list) is nondet
%% Print words that were found for respective WordSpaces.
%% Second parameter is list of word ids
print_words([],_).
print_words([WordSpaceId|WordSpaces], WordMasksData) :-
    get_dict(WordSpaceId, WordMasksData, Record),
    get_dict(chars, Record, Chars),
    get_dict(mask, Record, Mask),
    chars_to_mask_fill(Chars, MaskFill),
    word_mask(Mask,WordId, MaskFill),
    word(WordId, WordString),
    print(WordSpaceId),write(":"), print(WordString),nl,
    print_words(WordSpaces, WordMasksData).

%! generate_cross() is nondet
%% Main function for Crossword generation
generate_cross :-
    get_time_started(TimeStarted),
    get_time(TimeLoaded),
    findall(WordSpaceId, word_space(WordSpaceId, _, _), WordSpaceIds),
    initialize_word_masks(_{}, WordSpaceIds ,WordMasks),
    findall(CrossId, cross(_, _, _, _, CrossId), CrossIds),
    %print(CrossIds),nl,
    solve_crosses(WordMasks, CrossIds,  WordMasksOut),
    print_words(WordSpaceIds,WordMasksOut),
    %show_profile(),
    %print(WordMasksOut),
    %profile(call_with_time_limit(10,     ....   ))
    get_time(TimeEnded),
    LoadTime is TimeLoaded - TimeStarted,
    ComputeTime is TimeEnded - TimeLoaded,
    write("status:found"),nl,
    write("load_time:"),print(LoadTime),nl,
    write("compute_time:"),print(ComputeTime),nl,
    halt(0).

generate_cross :-
    get_time_started(TimeStarted),
    get_time(TimeLoaded),
    get_time(TimeEnded),
    LoadTime is TimeLoaded - TimeStarted,
    ComputeTime is TimeEnded - TimeLoaded,
    write("status:not_found"),nl,
    write("load_time:"),print(LoadTime),nl,
    write("compute_time:"),print(ComputeTime),nl,
    !, halt(1).
