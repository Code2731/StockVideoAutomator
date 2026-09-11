from app.version import is_newer, parse_version


def test_parse_version():
    assert parse_version("v1.2.3") == (1, 2, 3)
    assert parse_version("1.0") == (1, 0)
    assert parse_version("1.0.0-beta") == (1, 0, 0)
    assert parse_version("") == ()
    assert parse_version(None) == ()


def test_is_newer():
    assert is_newer("1.2.0", "1.1.9") is True
    assert is_newer("v2.0", "1.9.9") is True
    assert is_newer("1.0.0", "1.0.0") is False
    assert is_newer("1.0.0", "1.1.0") is False
    assert is_newer("", "1.0.0") is False
    assert is_newer("1.0.0", "") is False
