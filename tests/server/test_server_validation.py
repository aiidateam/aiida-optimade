import unittest

from optimade.validator import ImplementationValidator

from .utils import SetClient


class ServerTestWithValidator(SetClient, unittest.TestCase):
    """Use OPTIMADE Validator on server"""

    def test_with_validator(self):
        """Validate server"""
        validator = ImplementationValidator(client=self.client)
        try:
            validator.main()
        except Exception as exc:  # pylint: disable=broad-except
            print(repr(exc))
        self.assertTrue(validator.valid)
