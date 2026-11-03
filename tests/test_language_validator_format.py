# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from anura.services.language.validator import LanguageValidator


def test_language_code_format_rejects_trailing_newline() -> None:
    assert not LanguageValidator.is_valid_code_format("eng\n")
    assert not LanguageValidator.is_valid_code_format("eng\r\n")


def test_language_code_format_accepts_valid_codes() -> None:
    assert LanguageValidator.is_valid_code_format("eng")
    assert LanguageValidator.is_valid_code_format("chi_sim")
