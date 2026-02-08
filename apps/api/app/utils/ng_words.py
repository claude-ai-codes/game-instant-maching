import re

# === Exact-match NG words ===

NG_WORDS_JA: list[str] = [
    # 暴言・侮辱
    "死ね", "しね", "氏ね", "シネ",
    "殺す", "ころす", "コロス",
    "くたばれ", "クタバレ",
    "消えろ", "きえろ",
    "うざい", "ウザい", "うぜえ",
    "きもい", "キモい", "キモイ", "きめえ",
    "ガイジ", "がいじ",
    "池沼", "知障",
    "カス", "かす",
    "ゴミ", "ごみ",
    "クズ", "くず",
    "ボケ", "ぼけ",
    "アホ", "あほ",
    "バカ", "ばか", "馬鹿",
    "クソ", "くそ", "糞",
    "雑魚", "ざこ", "ザコ",
    "ノロマ", "のろま",
    "ブス", "ぶす",
    "デブ", "でぶ",
    "チビ", "ちび",
    "障害者",
    "気持ち悪い",
    # 差別
    "チョン", "シナ人",
    "土人", "部落",
    "在日",
    # 性的
    "セックス", "SEX",
    "エロ", "えろ",
    "おっぱい", "ちんこ", "まんこ",
    "オナニー",
    # 脅迫・犯罪
    "爆破", "放火",
    "通報する", "警察呼ぶ",
    "個人情報", "住所特定", "晒す", "さらす",
    "自殺しろ", "自殺しな",
]

NG_WORDS_EN: list[str] = [
    # Profanity
    "fuck", "fucker", "fucking",
    "shit", "shitty", "bullshit",
    "bitch", "asshole", "bastard",
    "damn", "dammit", "crap",
    "dick", "cock", "pussy",
    "whore", "slut",
    "piss", "pissed",
    "cunt",
    "motherfucker",
    "stfu", "gtfo", "kys",
    # Slurs
    "nigger", "nigga",
    "faggot", "fag",
    "retard", "retarded",
    "tranny",
    "chink", "gook", "spic",
    # Harassment
    "kill yourself",
    "go die",
    "neck yourself",
    "kms",
    # Spam-like
    "www.", "http://", "https://",
]

NG_WORDS = NG_WORDS_JA + NG_WORDS_EN

# === Regex patterns for obfuscation bypass ===

_OBFUSCATION_PATTERNS: list[str] = [
    # Japanese masked words: し◯ し〇 し○ etc.
    r"し[◯〇○ね]",
    r"ころ[◯〇○す]",
    r"く[◯〇○た]ばれ",
    r"死[◯〇○ね]",
    # English masked words: f*ck, fu*k, sh*t, etc.
    r"f[\*\.\-_]?[uU][\*\.\-_]?[cCkK][\*\.\-_]?[kK]?",
    r"sh[\*\.\-_]?[iI1][\*\.\-_]?t",
    r"b[\*\.\-_]?[iI1][\*\.\-_]?t[\*\.\-_]?ch",
    r"a[\*\.\-_]?s[\*\.\-_]?s[\*\.\-_]?h[\*\.\-_]?[oO0][\*\.\-_]?l[\*\.\-_]?e",
    r"n[\*\.\-_]?[iI1][\*\.\-_]?g[\*\.\-_]?g[\*\.\-_]?[eEaA3][\*\.\-_]?r?",
    r"f[\*\.\-_]?a[\*\.\-_]?g[\*\.\-_]?g?[\*\.\-_]?[oO0]?t?",
    r"r[\*\.\-_]?[eE3][\*\.\-_]?t[\*\.\-_]?a[\*\.\-_]?r[\*\.\-_]?d",
    # Leetspeak substitutions
    r"[fF][uU][cCkK]{1,2}",
    r"[sS][hH][iI1][tT]",
    r"[kK][yY][sS]",
]

# Build combined pattern
_exact_pattern = "|".join(re.escape(w) for w in NG_WORDS)
_obfuscation_pattern = "|".join(_OBFUSCATION_PATTERNS)
_NG_PATTERN = re.compile(f"({_exact_pattern})|({_obfuscation_pattern})", re.IGNORECASE)

URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


def contains_ng_word(text: str) -> bool:
    return bool(_NG_PATTERN.search(text))


def contains_url(text: str) -> bool:
    return bool(URL_PATTERN.search(text))
