"""add games table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-07 23:45:00.000000
"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_GAMES = [
    # FPS
    ("valorant", "VALORANT", "ヴァロラント", "fps", ["pc"]),
    ("apex_legends", "Apex Legends", "エーペックスレジェンズ", "fps", ["pc", "ps", "xbox", "switch"]),
    ("overwatch2", "Overwatch 2", "オーバーウォッチ2", "fps", ["pc", "ps", "xbox", "switch"]),
    ("fortnite", "Fortnite", "フォートナイト", "fps", ["pc", "ps", "xbox", "switch", "mobile"]),
    ("counter_strike2", "Counter-Strike 2", "カウンターストライク2", "fps", ["pc"]),
    ("rainbow_six_siege", "Rainbow Six Siege", "レインボーシックス シージ", "fps", ["pc", "ps", "xbox"]),
    ("call_of_duty_warzone", "Call of Duty: Warzone", "コール オブ デューティ ウォーゾーン", "fps", ["pc", "ps", "xbox"]),
    ("call_of_duty_bo6", "Call of Duty: Black Ops 6", "コール オブ デューティ BO6", "fps", ["pc", "ps", "xbox"]),
    ("battlefield_2042", "Battlefield 2042", "バトルフィールド2042", "fps", ["pc", "ps", "xbox"]),
    ("xdefiant", "XDefiant", "エックスディファイアント", "fps", ["pc", "ps", "xbox"]),
    ("the_finals", "THE FINALS", "ザ・ファイナルズ", "fps", ["pc", "ps", "xbox"]),
    ("deadlock", "Deadlock", "デッドロック", "fps", ["pc"]),
    ("marvel_rivals", "Marvel Rivals", "マーベル ライバルズ", "fps", ["pc", "ps", "xbox"]),
    ("spectre_divide", "Spectre Divide", "スペクター ディバイド", "fps", ["pc"]),
    # TPS
    ("splatoon3", "Splatoon 3", "スプラトゥーン3", "tps", ["switch"]),
    # MOBA
    ("league_of_legends", "League of Legends", "リーグ・オブ・レジェンド", "moba", ["pc"]),
    ("dota2", "Dota 2", None, "moba", ["pc"]),
    ("pokemon_unite", "Pokemon UNITE", "ポケモンユナイト", "moba", ["switch", "mobile"]),
    ("wild_rift", "League of Legends: Wild Rift", "ワイルドリフト", "moba", ["mobile"]),
    ("honor_of_kings", "Honor of Kings", None, "moba", ["mobile"]),
    # Battle Royale
    ("pubg", "PUBG: BATTLEGROUNDS", None, "battle_royale", ["pc", "ps", "xbox", "mobile"]),
    ("fall_guys", "Fall Guys", "フォールガイズ", "battle_royale", ["pc", "ps", "xbox", "switch"]),
    # Fighting
    ("street_fighter6", "Street Fighter 6", "ストリートファイター6", "fighting", ["pc", "ps", "xbox"]),
    ("tekken8", "Tekken 8", "鉄拳8", "fighting", ["pc", "ps", "xbox"]),
    ("guilty_gear_strive", "Guilty Gear Strive", "ギルティギア ストライヴ", "fighting", ["pc", "ps", "xbox"]),
    ("granblue_fantasy_versus_rising", "Granblue Fantasy Versus: Rising", "グランブルーファンタジー ヴァーサス ライジング", "fighting", ["pc", "ps"]),
    ("dragon_ball_sparking_zero", "Dragon Ball: Sparking! Zero", "ドラゴンボール Sparking! ZERO", "fighting", ["pc", "ps", "xbox"]),
    # RPG / MMO
    ("ff14", "Final Fantasy XIV", "ファイナルファンタジー14", "mmorpg", ["pc", "ps", "xbox"]),
    ("genshin_impact", "Genshin Impact", "原神", "rpg", ["pc", "ps", "mobile"]),
    ("honkai_star_rail", "Honkai: Star Rail", "崩壊：スターレイル", "rpg", ["pc", "ps", "mobile"]),
    ("zenless_zone_zero", "Zenless Zone Zero", "ゼンレスゾーンゼロ", "rpg", ["pc", "ps", "mobile"]),
    ("monster_hunter_wilds", "Monster Hunter Wilds", "モンスターハンター ワイルズ", "rpg", ["pc", "ps", "xbox"]),
    ("monster_hunter_rise", "Monster Hunter Rise", "モンスターハンターライズ", "rpg", ["pc", "ps", "xbox", "switch"]),
    ("pso2_ngs", "Phantasy Star Online 2: New Genesis", "PSO2 ニュージェネシス", "mmorpg", ["pc", "ps", "switch"]),
    ("blue_protocol", "Blue Protocol", "ブループロトコル", "mmorpg", ["pc"]),
    ("destiny2", "Destiny 2", "デスティニー2", "rpg", ["pc", "ps", "xbox"]),
    ("diablo4", "Diablo IV", "ディアブロ IV", "rpg", ["pc", "ps", "xbox"]),
    ("elden_ring", "Elden Ring", "エルデンリング", "rpg", ["pc", "ps", "xbox"]),
    # Card
    ("hearthstone", "Hearthstone", "ハースストーン", "card", ["pc", "mobile"]),
    ("shadowverse", "Shadowverse", "シャドウバース", "card", ["pc", "mobile"]),
    ("master_duel", "Yu-Gi-Oh! Master Duel", "遊戯王 マスターデュエル", "card", ["pc", "ps", "xbox", "switch", "mobile"]),
    ("pokemon_tcg_pocket", "Pokemon TCG Pocket", "ポケモンカードゲーム Pocket", "card", ["mobile"]),
    # Sports / Racing
    ("rocket_league", "Rocket League", "ロケットリーグ", "sports", ["pc", "ps", "xbox", "switch"]),
    ("fc25", "EA Sports FC 25", None, "sports", ["pc", "ps", "xbox", "switch"]),
    ("gran_turismo7", "Gran Turismo 7", "グランツーリスモ7", "racing", ["ps"]),
    # Survival / Sandbox
    ("minecraft", "Minecraft", "マインクラフト", "sandbox", ["pc", "ps", "xbox", "switch", "mobile"]),
    ("ark_survival_ascended", "ARK: Survival Ascended", None, "survival", ["pc", "ps", "xbox"]),
    ("rust", "Rust", None, "survival", ["pc", "ps", "xbox"]),
    ("palworld", "Palworld", "パルワールド", "survival", ["pc", "xbox"]),
    # Strategy
    ("civ6", "Sid Meier's Civilization VI", "シヴィライゼーション VI", "strategy", ["pc", "ps", "xbox", "switch"]),
    ("age_of_empires4", "Age of Empires IV", "エイジ オブ エンパイア IV", "strategy", ["pc", "xbox"]),
    # Horror / Co-op
    ("dead_by_daylight", "Dead by Daylight", "デッド バイ デイライト", "horror", ["pc", "ps", "xbox", "switch", "mobile"]),
    ("phasmophobia", "Phasmophobia", "ファズモフォビア", "horror", ["pc", "ps", "xbox"]),
    ("lethal_company", "Lethal Company", "リーサルカンパニー", "horror", ["pc"]),
    # Other
    ("among_us", "Among Us", "アモングアス", "party", ["pc", "ps", "xbox", "switch", "mobile"]),
    ("other", "Other", "その他", "other", []),
]


def upgrade() -> None:
    op.create_table(
        "games",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("name_ja", sa.String(100), nullable=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("platform_tags", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_games_slug", "games", ["slug"])
    op.create_index("ix_games_category", "games", ["category"])

    # Seed initial games
    games_table = sa.table(
        "games",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("name_ja", sa.String),
        sa.column("category", sa.String),
        sa.column("platform_tags", sa.JSON),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        games_table,
        [
            {
                "id": str(uuid.uuid4()),
                "slug": slug,
                "name": name,
                "name_ja": name_ja,
                "category": category,
                "platform_tags": platform_tags,
                "is_active": True,
            }
            for slug, name, name_ja, category, platform_tags in SEED_GAMES
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_games_category", table_name="games")
    op.drop_index("ix_games_slug", table_name="games")
    op.drop_table("games")
