import html
import json
from pathlib import Path

_SHARED = Path(__file__).resolve().parents[4] / "packages" / "shared"

with open(_SHARED / "games.json") as f:
    GAMES = json.load(f)
VALID_GAME_IDS = {g["id"] for g in GAMES}

with open(_SHARED / "regions.json") as f:
    REGIONS = json.load(f)
VALID_REGION_IDS = {r["id"] for r in REGIONS}


def sanitize_text(text: str) -> str:
    return html.escape(text.strip())


def validate_game(game: str) -> bool:
    return game in VALID_GAME_IDS


def validate_region(region: str) -> bool:
    return region in VALID_REGION_IDS
