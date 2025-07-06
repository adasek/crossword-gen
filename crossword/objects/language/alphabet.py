from typing import (Callable, Dict, FrozenSet, Generic, List, ParamSpec, Set,
                    Tuple, TypeVar, cast)

from icu import Collator  # type: ignore # pylint: disable=no-name-in-module
from icu import Locale, LocaleData

P = ParamSpec("P")
R = TypeVar("R")

class Memoize(Generic[P, R]):
    """A decorator class to memoize function calls with arguments and keyword arguments."""
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
    collator = Collator.createInstance(Locale(locale_code))  # type: ignore
    return sorted(
        list(alphabet_set(locale_code=locale_code, only_characters=False)),
        key=collator.getSortKey  # type: ignore
    )


@Memoize
def alphabet_set(locale_code: str, only_characters: bool = False) -> Set[str]:
    """Returns alphabet as a set of characters or clusters."""
    locale_data = LocaleData(locale_code) # type: ignore
    if only_characters:
        return set(list("".join(locale_data.getExemplarSet()))) # type: ignore

    return set(locale_data.getExemplarSet()) # type: ignore
