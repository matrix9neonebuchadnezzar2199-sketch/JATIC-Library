"""51-region master for typeB downloads."""

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class Region(StrEnum):
    """Geographic grouping for UI bulk selection."""

    HOKKAIDO = "北海道"
    TOHOKU = "東北"
    KANTO = "関東"
    CHUBU = "中部"
    KANSAI = "関西"
    CHUGOKU = "中国"
    SHIKOKU = "四国"
    KYUSHU = "九州"
    OKINAWA = "沖縄"


@dataclass(frozen=True)
class Target:
    """One downloadable region entry."""

    code: str
    display_name: str
    folder_label: str
    region: Region
    filename_key: str
    order: int


TARGETS: tuple[Target, ...] = (
    Target("hokkaido_sapporo", "北海道(札幌方面)", "北海道_札幌方面", Region.HOKKAIDO, "hokkaido_sapporo", 1),
    Target("hokkaido_hakodate", "北海道(函館方面)", "北海道_函館方面", Region.HOKKAIDO, "hokkaido_hakodate", 2),
    Target("hokkaido_asahikawa", "北海道(旭川方面)", "北海道_旭川方面", Region.HOKKAIDO, "hokkaido_asahikawa", 3),
    Target("hokkaido_kushiro", "北海道(釧路方面)", "北海道_釧路方面", Region.HOKKAIDO, "hokkaido_kushiro", 4),
    Target("hokkaido_kitami", "北海道(北見方面)", "北海道_北見方面", Region.HOKKAIDO, "hokkaido_kitami", 5),
    Target("aomori", "青森県", "青森県", Region.TOHOKU, "aomori", 6),
    Target("iwate", "岩手県", "岩手県", Region.TOHOKU, "iwate", 7),
    Target("miyagi", "宮城県", "宮城県", Region.TOHOKU, "miyagi", 8),
    Target("akita", "秋田県", "秋田県", Region.TOHOKU, "akita", 9),
    Target("yamagata", "山形県", "山形県", Region.TOHOKU, "yamagata", 10),
    Target("fukushima", "福島県", "福島県", Region.TOHOKU, "fukushima", 11),
    Target("ibaraki", "茨城県", "茨城県", Region.KANTO, "ibaraki", 12),
    Target("tochigi", "栃木県", "栃木県", Region.KANTO, "tochigi", 13),
    Target("gunma", "群馬県", "群馬県", Region.KANTO, "gunma", 14),
    Target("saitama", "埼玉県", "埼玉県", Region.KANTO, "saitama", 15),
    Target("chiba", "千葉県", "千葉県", Region.KANTO, "chiba", 16),
    Target("tokyo", "東京都", "東京都", Region.KANTO, "tokyo", 17),
    Target("kanagawa", "神奈川県", "神奈川県", Region.KANTO, "kanagawa", 18),
    Target("yamanashi", "山梨県", "山梨県", Region.KANTO, "yamanashi", 19),
    Target("nagano", "長野県", "長野県", Region.CHUBU, "nagano", 20),
    Target("niigata", "新潟県", "新潟県", Region.CHUBU, "niigata", 21),
    Target("toyama", "富山県", "富山県", Region.CHUBU, "toyama", 22),
    Target("ishikawa", "石川県", "石川県", Region.CHUBU, "ishikawa", 23),
    Target("fukui", "福井県", "福井県", Region.CHUBU, "fukui", 24),
    Target("gifu", "岐阜県", "岐阜県", Region.CHUBU, "gifu", 25),
    Target("shizuoka", "静岡県", "静岡県", Region.CHUBU, "shizuoka", 26),
    Target("aichi", "愛知県", "愛知県", Region.CHUBU, "aichi", 27),
    Target("mie", "三重県", "三重県", Region.KANSAI, "mie", 28),
    Target("shiga", "滋賀県", "滋賀県", Region.KANSAI, "shiga", 29),
    Target("kyoto", "京都府", "京都府", Region.KANSAI, "kyoto", 30),
    Target("osaka", "大阪府", "大阪府", Region.KANSAI, "osaka", 31),
    Target("hyogo", "兵庫県", "兵庫県", Region.KANSAI, "hyogo", 32),
    Target("nara", "奈良県", "奈良県", Region.KANSAI, "nara", 33),
    Target("wakayama", "和歌山県", "和歌山県", Region.KANSAI, "wakayama", 34),
    Target("tottori", "鳥取県", "鳥取県", Region.CHUGOKU, "tottori", 35),
    Target("shimane", "島根県", "島根県", Region.CHUGOKU, "shimane", 36),
    Target("okayama", "岡山県", "岡山県", Region.CHUGOKU, "okayama", 37),
    Target("hiroshima", "広島県", "広島県", Region.CHUGOKU, "hiroshima", 38),
    Target("yamaguchi", "山口県", "山口県", Region.CHUGOKU, "yamaguchi", 39),
    Target("tokushima", "徳島県", "徳島県", Region.SHIKOKU, "tokushima", 40),
    Target("kagawa", "香川県", "香川県", Region.SHIKOKU, "kagawa", 41),
    Target("ehime", "愛媛県", "愛媛県", Region.SHIKOKU, "ehime", 42),
    Target("kochi", "高知県", "高知県", Region.SHIKOKU, "kochi", 43),
    Target("fukuoka", "福岡県", "福岡県", Region.KYUSHU, "fukuoka", 44),
    Target("saga", "佐賀県", "佐賀県", Region.KYUSHU, "saga", 45),
    Target("nagasaki", "長崎県", "長崎県", Region.KYUSHU, "nagasaki", 46),
    Target("kumamoto", "熊本県", "熊本県", Region.KYUSHU, "kumamoto", 47),
    Target("oita", "大分県", "大分県", Region.KYUSHU, "oita", 48),
    Target("miyazaki", "宮崎県", "宮崎県", Region.KYUSHU, "miyazaki", 49),
    Target("kagoshima", "鹿児島県", "鹿児島県", Region.KYUSHU, "kagoshima", 50),
    Target("okinawa", "沖縄県", "沖縄県", Region.OKINAWA, "okinawa", 51),
)

_CODE_INDEX: dict[str, Target] = {t.code: t for t in TARGETS}


def by_code(code: str) -> Target:
    """Return target by internal code."""
    try:
        return _CODE_INDEX[code]
    except KeyError as exc:
        raise KeyError(f"Unknown target code: {code}") from exc


def by_region(region: Region) -> list[Target]:
    """Return all targets in a region, sorted by order."""
    return sorted((t for t in TARGETS if t.region == region), key=lambda t: t.order)


def all_targets() -> tuple[Target, ...]:
    """Return the built-in target master tuple."""
    return TARGETS


def all_codes() -> list[str]:
    """Return every target code in display order."""
    return [t.code for t in TARGETS]


def _apply_overrides(base: tuple[Target, ...], overrides: dict[str, str]) -> tuple[Target, ...]:
    updated: list[Target] = []
    for target in base:
        key = overrides.get(target.code)
        if key is not None:
            updated.append(
                Target(
                    target.code,
                    target.display_name,
                    target.folder_label,
                    target.region,
                    key,
                    target.order,
                )
            )
        else:
            updated.append(target)
    return tuple(updated)


def load_overrides(cache_path: Path) -> tuple[Target, ...]:
    """Load targets with optional filename_key overrides from JSON cache."""
    if not cache_path.is_file():
        return TARGETS
    try:
        raw: dict[str, Any] = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return TARGETS
    entries = raw.get("targets", [])
    if not isinstance(entries, list):
        return TARGETS
    overrides: dict[str, str] = {}
    for item in entries:
        if isinstance(item, dict) and "code" in item and "filename_key" in item:
            overrides[str(item["code"])] = str(item["filename_key"])
    return _apply_overrides(TARGETS, overrides)


def save_overrides(targets: list[Target], cache_path: Path) -> None:
    """Persist filename_key overrides for later loads."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "scraped_at": None,
        "targets": [{"code": t.code, "filename_key": t.filename_key} for t in targets],
    }
    cache_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
