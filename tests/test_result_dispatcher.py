# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest
from unittest.mock import patch

from anura.services.result_dispatcher import ResultDispatcher

class TestResultDispatcher:
    @pytest.fixture
    def dispatcher(self):
        return ResultDispatcher()

    def test_dispatch_empty_text(self, dispatcher):
        result = dispatcher.dispatch("")
        assert result.text == ""
        assert result.urls == ()
        assert result.is_primary_url is False

    def test_dispatch_regular_text(self, dispatcher):
        text = "Hello world"
        result = dispatcher.dispatch(text)
        assert result.text == text
        assert result.urls == ()
        assert result.is_primary_url is False

    def test_dispatch_primary_url(self, dispatcher):
        url = "https://example.com"
        result = dispatcher.dispatch(url)
        assert result.text == url
        assert url in result.urls
        assert result.is_primary_url is True

    def test_dispatch_text_with_structured_data(self, dispatcher):
        text = "Contact us at info@example.com or visit https://example.com"
        result = dispatcher.dispatch(text)
        assert result.text == text
        assert "info@example.com" in result.emails
        assert "https://example.com" in result.urls
        assert result.is_primary_url is False
