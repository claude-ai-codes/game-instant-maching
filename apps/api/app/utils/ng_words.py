import re

NG_WORDS: list[str] = [
    "死ね",
    "殺す",
    "くたばれ",
    "ガイジ",
    "きもい",
    "キモい",
    "fuck",
    "shit",
    "nigger",
    "faggot",
]

_NG_PATTERN = re.compile("|".join(re.escape(w) for w in NG_WORDS), re.IGNORECASE)

URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


def contains_ng_word(text: str) -> bool:
    return bool(_NG_PATTERN.search(text))


def contains_url(text: str) -> bool:
    return bool(URL_PATTERN.search(text))
