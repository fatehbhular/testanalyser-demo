import pytest

def test_addition_passes():
    assert 2 + 2 == 4

def test_addition_fails():
    assert 2 + 2 == 5

@pytest.mark.skip(reason="Demonstrated of a skipped test")
def test_feature_skipped():
    assert True