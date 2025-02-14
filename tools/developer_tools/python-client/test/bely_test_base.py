import unittest
import uuid

from BelyApiFactory import BelyApiFactory


class BelyTestBase(unittest.TestCase):
    TEST_USER_USERNAME = "user"
    TEST_USER_PASSWORD = "user"
    ADMIN_USERNAME = "logr"
    ADMIN_PASSWORD = "logr"

    CTL_LOGBOOK_ID = 6
    OPS_LOGBOOK_ID = 4
    DOC_TEMPLATE_COPY_ID = 1
    DOC_TEMPLATE_PER_ENTRY_ID = 2
    DOC_TEMPLATE_SECTIONS_COPY_ID = 78

    DOC_SAMPLE_ID = 82
    DOC_WITH_ENTRIES = 83

    TEST_DOCUMENT_ID = 3

    def setUp(self):
        self.factory = BelyApiFactory("http://127.0.0.1:8080/bely")

        self.logbook_api = self.factory.get_lobook_api()

        self.loggedIn = False

    def tearDown(self):
        if self.loggedIn:
            self.factory.logout_user()

    def login_as_admin(self):
        if self.loggedIn:
            self.factory.logout_user()
        self.loggedIn = True
        self.factory.authenticate_user(self.ADMIN_USERNAME, self.ADMIN_PASSWORD)

    def login_as_user(self):
        if self.loggedIn:
            self.factory.logout_user()
        self.loggedIn = True
        self.factory.authenticate_user(self.TEST_USER_USERNAME, self.TEST_USER_PASSWORD)

    def _gen_unique_name(self):
        return uuid.uuid4().hex[:10]
