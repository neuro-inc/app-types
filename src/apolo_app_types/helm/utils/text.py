import difflib
import re


def normalize(text: str) -> str:
    # Remove non-alphanumerics and lowercase
    return re.sub(r"[^a-zA-Z0-9]", "", text).lower()


def fuzzy_contains(needle: str, haystack: str, cutoff: float = 0.8) -> bool:
    norm_needle = normalize(needle)
    norm_haystack = normalize(haystack)

    # Check direct containment
    if norm_needle in norm_haystack:
        return True

    # Fuzzy check with sliding window
    matches = difflib.get_close_matches(
        norm_needle, [norm_haystack], n=1, cutoff=cutoff
    )
    return bool(matches)
