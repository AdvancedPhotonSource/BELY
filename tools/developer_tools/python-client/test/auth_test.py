from tkinter.messagebox import NO
import unittest

from BelyApiFactory import BelyApiFactory
from belyApi import LogDocumentOptions, OpenApiException
from test.bely_test_base import BelyTestBase


class AuthTests(BelyTestBase):

    def test_verify_admin_auth(self):
        self.login_as_admin()
        self.factory.auth_api.verify_authenticated()

    def test_verify_user_auth(self):
        self.login_as_user()
        self.factory.auth_api.verify_authenticated()


if __name__ == "__main__":
    unittest.main()
