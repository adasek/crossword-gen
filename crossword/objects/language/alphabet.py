from typing import (Callable, Dict, FrozenSet, Generic, List, ParamSpec, Set,
                    Tuple, TypeVar, cast)

from icu import Collator, Locale, LocaleData  # type: ignore

P = ParamSpec("P")
R = TypeVar("R")

class Memoize(Generic[P, R]):
    def __init__(self, fn: Callable[P, R]) -> None:
        self.fn = fn
        self.memo: Dict[
            Tuple[Tuple[object, ...], FrozenSet[Tuple[str, object]]],
            R
        ] = {}

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        key = (
            cast(Tuple[object, ...], args),
            frozenset(kwargs.items())
        )
        if key not in self.memo:
            self.memo[key] = self.fn(*args, **kwargs)
        return self.memo[key]

# https://stackoverflow.com/questions/52045659/how-to-get-the-current-locales-alphabet-in-python-3
# https://unicode-org.github.io/cldr-staging/charts/latest/by_type/core_data.alphabetic_information.main.html
# https://stackoverflow.com/questions/1097908/how-do-i-sort-unicode-strings-alphabetically-in-python
@Memoize
def alphabet(locale_code: str) -> List[str]:
    """
    List unique characters in the given locale

    Args:
        locale_code: ISO 639-1 language specification (e.g. 'en', 'cs')

    Returns:
        List of different characters(including clusters) for the given locale alphabetically sorted
    """
    collator = Collator.createInstance(Locale(locale_code))
    return sorted(list(alphabet_set(locale_code=locale_code, only_characters=False)), key=collator.getSortKey)


@Memoize
def alphabet_set(locale_code: str, only_characters: bool = False) -> Set[str]:
    locale_data = LocaleData(locale_code)
    if only_characters:
        return set(list("".join(locale_data.getExemplarSet())))
    else:
        return set(locale_data.getExemplarSet())


@Memoize
def alphabet_multiletters_from_singleletters(locale_code: str) -> bool:
    single_letters = [singleletter for singleletter in alphabet_set(locale_code) if len(singleletter) == 1]
    return len(alphabet_set(locale_code, only_characters=True)) == len(single_letters)
