"""Tests for module constants."""

from jatic_library import constants as c


def test_app_identity() -> None:
    assert c.APP_NAME == "JATIC-Library"
    assert c.APP_VERSION == "0.1.0-beta.1"


def test_jartic_urls() -> None:
    assert c.JARTIC_BASE == "https://www.jartic.or.jp"
    assert c.JARTIC_OPENDATA_PAGE.endswith("/service/opendata/")
    assert "{publish_ym_compact}" in c.JARTIC_DATA_DIR_TPL
    assert "{filename_key}" in c.JARTIC_ZIP_TPL
