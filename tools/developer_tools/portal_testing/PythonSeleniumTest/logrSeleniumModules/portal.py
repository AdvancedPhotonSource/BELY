#!/usr/bin/env python

"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

from logrSeleniumModules.logrSeleniumModuleBase import LogrSeleniumModuleBase

CDB_LOGIN = 'logr'
CDB_PASSWORD = 'logr'
LOGIN_BUTTON_ID = 'loginButton'
LOGOUT_BUTTON_ID = 'logoutButton'


class Portal(LogrSeleniumModuleBase):

	def login(self, login=CDB_LOGIN, password=CDB_PASSWORD):
		self._click_on_id(LOGIN_BUTTON_ID)

		self._type_in_id('loginForm:username', login)
		self._type_in_id('loginForm:password', password)
		self._click_on_id('loginForm:loginButton')

		self._wait_for_id(LOGOUT_BUTTON_ID)

	def logout(self):
		self._clear_notifications()
		self._click_on_id(LOGOUT_BUTTON_ID)
		self._wait_for_id(LOGIN_BUTTON_ID)