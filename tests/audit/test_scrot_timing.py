from unittest.mock import MagicMock, patch


def test_legacy_x11_provider_timing_race(headless_gi_mocks):
    """[NEW-016] Verify that scrot polling handles slow disk flush via increased retries."""

    from anura.services.screenshot.legacy_provider import LegacyX11Provider

    provider = LegacyX11Provider()

    mock_proc = MagicMock()
    mock_proc.get_if_exited.return_value = True
    mock_proc.get_exit_status.return_value = 0

    mock_callback = MagicMock()
    output_path = "/tmp/test-shot.png"

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.stat") as mock_stat,
        patch("time.sleep") as mock_sleep,
    ):
        mock_stat.return_value.st_size = 0
        mock_proc.wait_finish = MagicMock()

        provider._on_finish(mock_proc, MagicMock(), (mock_callback, output_path))

        args, _kwargs = mock_callback.call_args
        assert args[0] is False
        assert "no output" in args[2]
        # NEW-016: Implementation now retries 50 times (49 sleeps)
        assert mock_sleep.call_count == 49
