# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

from anura.services.language.validator import LanguageValidator


@pytest.mark.parametrize("code", ["eng\\n", "ita\\n", "chi_sim\\n"])
def test_language_validator_rejects_trailing_newline(code: str) -> None:
    assert LanguageValidator.is_valid_code(code) is False
    assert LanguageValidator.is_valid_code_format(code) is False


@pytest.mark.parametrize("code", ["eng", "ita", "chi_sim", "aze_cyrl"])
def test_language_validator_accepts_valid_codes(code: str) -> None:
    assert LanguageValidator.is_valid_code(code) is True
    assert LanguageValidator.is_valid_code_format(code) is True
