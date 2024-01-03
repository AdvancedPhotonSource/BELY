#!/usr/bin/env python

"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""
import os
import unittest

from selenium import webdriver

from logrSeleniumModules.portal import Portal
from logrSeleniumModules.propertyType import PropertyType
from logrSeleniumModules.user_info import UserInfo


class CdbPortalFunctionalTestSuite(unittest.TestCase):

    PORTAL_URL = 'http://localhost:8080/logr'    

    DATA_PATH = "%s/data-dw" % os.getcwd()

    def setUp(self):
        self.prepare_download_area()
        opts = webdriver.ChromeOptions()
        prefs = {"download.default_directory": self.DATA_PATH}
        opts.add_experimental_option("prefs", prefs)
        
        headless = os.getenv("CDB_TEST_HEADLESS", 'False').lower() in ('true', '1', 't', 'y', 'yes')
        if headless:
            opts.add_argument("headless")

        self.driver = webdriver.Chrome(options=opts)
        self.driver.set_window_position(0, 0)
        self.driver.maximize_window()
        self.driver.get(self.PORTAL_URL)

        self.portal = Portal(self.driver)
        self.property_type = PropertyType(self.driver)
        self.user_info = UserInfo(self.driver)

        self.portal.login()

    def tearDown(self):
        self.portal.logout()
        self.driver.close()

    def prepare_download_area(self):
        if os.path.exists(self.DATA_PATH):
            # Clean up any residual downloads
            for file in os.scandir(self.DATA_PATH):
                os.remove(file.path)
        else:
            # Create directory
            os.mkdir(self.DATA_PATH)

    def verify_file_downloaded(self, file_name):
        file_path = "%s/%s" % (self.DATA_PATH, file_name)
        exits = os.path.exists(file_path)
        self.assertEqual(True, exits, msg='Downloaded file %s was not found' % file_name)

    def test_create_property_type(self):
        self.property_type.add_sample_test_property_type()
        self.property_type.delete_sample_test_property_type()

    def test_user_info_pages(self):
        self.user_info.navigate_to_user_info_list()
        self.user_info.test_user_info_pages()

    def test_user_info_export(self):
        self.user_info.navigate_to_user_info_list()
        self.user_info.export_user_info(self)


if __name__ == '__main__':
    unittest.main()