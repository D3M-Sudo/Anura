from anura.utils.validators import is_safe_url_string

def test_legitimate_cyrillic_url_regression():
    # Purely Cyrillic domain should be allowed
    url = "https://пример.рф"
    assert is_safe_url_string(url) is True

def test_homograph_mixed_script_regression():
    # Mixed script in the SAME label should be rejected
    url = "https://exаmple.com" # Cyrillic 'а'
    assert is_safe_url_string(url) is False

def test_legitimate_german_url():
    url = "https://münchen.de"
    assert is_safe_url_string(url) is True
