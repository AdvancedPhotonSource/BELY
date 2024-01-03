#!/usr/bin/env python

"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from logrSeleniumModules.logrSeleniumModuleBase import LogrSeleniumModuleBase


class ItemBase(LogrSeleniumModuleBase):

	def delete_current_item(self):
		self._click_on_id('componentViewForm:componentViewDeleteButton')
		confirmButton = self._find_by_id('componentViewForm:componentDestroyDialogYesConfirmButton')
		confirmButton.click()

		WebDriverWait(self.driver, LogrSeleniumModuleBase.WAIT_FOR_ELEMENT_TIMEOUT).until(EC.url_contains('/list'))