import pytest

from optimade.validator import ImplementationValidator


@pytest.mark.skip("Does not comply with OPTIMADE validator")
def test_with_validator(client):
    """Validate server"""
    validator = ImplementationValidator(client=client)
    try:
        validator.main()
    except Exception as exc:  # pylint: disable=broad-except
        print(repr(exc))

    assert validator.valid
