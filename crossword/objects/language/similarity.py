
def similar_strings(str1: str, str2: str) -> bool:
    # normalize
    str1 = str1.lower()
    str2 = str2.lower()
    for ai in range(len(str1) - 3):
        for bi in range(len(str2) - 3):
            if str1[ai:ai + 3] == str2[bi:bi + 3]:
                return True
    return False


def contains_string(str1: str, str2: str) -> bool:
    # normalize
    str1 = str1.lower().strip()
    str2 = str2.lower()
    return str1 in str2
