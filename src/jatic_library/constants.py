"""Application-wide constants."""

from pathlib import Path

APP_NAME = "JATIC-Library"
APP_VERSION = "0.1.0-beta.1"
ORG_NAME = "matrix9neonebuchadnezzar2199-sketch"
REPO_URL = "https://github.com/matrix9neonebuchadnezzar2199-sketch/JATIC-Library"

JARTIC_BASE = "https://www.jartic.or.jp"
JARTIC_OPENDATA_PAGE = f"{JARTIC_BASE}/service/opendata/"
JARTIC_DATA_DIR_TPL = JARTIC_BASE + "/d/opendata/{publish_ym_compact}/"
JARTIC_ZIP_TPL = JARTIC_DATA_DIR_TPL + "typeB_{filename_key}.zip"

PUBLISH_LAG_MONTHS = 2

DEFAULT_CHECK_INTERVAL_HOURS = 24
DEFAULT_CONCURRENCY = 3
DEFAULT_RETRY = 3
DEFAULT_TIMEOUT_SEC = 60
APP_DATA_DIR = Path.home() / "AppData" / "Local" / APP_NAME
CONFIG_PATH = APP_DATA_DIR / "config.json"
DB_PATH = APP_DATA_DIR / "history.db"
LOG_DIR = APP_DATA_DIR / "logs"
TARGETS_CACHE_PATH = APP_DATA_DIR / "targets.json"
LIBRARY_SCAN_CACHE_PATH = APP_DATA_DIR / "library_scan_cache.json"

MANIFEST_FILENAME = "_manifest.json"
EXTRACTED_DIR_NAME = "extracted"
MERGED_CSV_FILENAME = "統合.csv"
MERGED_CSV_DISPLAY_NAME = "統合CSV"
# Shift_JIS (Windows cp932) for Excel double-click on Japanese Windows.
MERGED_CSV_ENCODING = "cp932"

TZ_JST = "Asia/Tokyo"
