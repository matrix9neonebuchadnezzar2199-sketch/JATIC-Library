"""Tests for publication status derivation after downloads."""

from jatic_library.core.downloader import DownloadResult, publication_status_for_result


def test_complete_when_all_targets_finished() -> None:
    result = DownloadResult(
        publish_ym="2026_3",
        succeeded=["tokyo"],
        skipped=["osaka"],
    )
    assert publication_status_for_result(result, target_count=2) == "complete"


def test_partial_when_some_failed() -> None:
    result = DownloadResult(
        publish_ym="2026_3",
        succeeded=["tokyo"],
        failed=[("osaka", "404")],
    )
    assert publication_status_for_result(result, target_count=2) == "partial"


def test_partial_when_subset_succeeded_without_failure() -> None:
    """One region OK must not mark a 51-region job as complete."""
    result = DownloadResult(publish_ym="2026_3", succeeded=["tokyo"])
    assert publication_status_for_result(result, target_count=51) == "partial"


def test_pending_when_nothing_done() -> None:
    result = DownloadResult(publish_ym="2026_3")
    assert publication_status_for_result(result, target_count=3) == "pending"
