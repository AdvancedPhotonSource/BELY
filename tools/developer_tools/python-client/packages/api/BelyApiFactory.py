#!/usr/bin/env python

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.

# Annotations are stored as strings so that the API return types below can be
# named without importing them at module load time.
from __future__ import annotations

import base64
import os
import warnings
import typing

if typing.TYPE_CHECKING:
    from belyApi import (
        AuthenticationApi,
        DomainApi,
        DownloadsApi,
        LogbookApi,
        NotificationConfigurationApi,
        PropertyValueApi,
        SearchApi,
        SystemLogApi,
        UsersApi,
    )


class BelyApiFactory:

    HEADER_TOKEN_KEY = "token"
    URL_FORMAT = "%s/views/item/view?id=%s"

    LOGBOOK_DOMAIN_ID = 1

    # attribute name -> generated api class. Each api is built on first access by
    # __getattr__ so that importing this module does not drag in every belyApi
    # model; see the "Known startup cost" section of bely-cli/CLAUDE.md. The
    # generator's lazyImports option only pays off while this stays lazy.
    _API_CLASSES = {
        "auth_api": "AuthenticationApi",
        "domain_api": "DomainApi",
        "downloads_api": "DownloadsApi",
        "logbook_api": "LogbookApi",
        "notification_configuration_api": "NotificationConfigurationApi",
        "property_value_api": "PropertyValueApi",
        "search_api": "SearchApi",
        "systemlog_api": "SystemLogApi",
        "users_api": "UsersApi",
    }

    # Deprecated camelCase aliases -> canonical attribute name
    _API_ALIASES = {
        "domainApi": "domain_api",
        "downloadsApi": "downloads_api",
        "propertyValueApi": "property_value_api",
        "searchApi": "search_api",
        "systemlogApi": "systemlog_api",
        "usersApi": "users_api",
    }

    def __init__(self, bely_url):
        from belyApi import ApiClient, Configuration

        self.bely_url = bely_url
        self.config = Configuration(host=self.bely_url)
        self.api_client = ApiClient(configuration=self.config)

    def __getattr__(self, name):
        """Build api instances on first access.

        Only called when normal attribute lookup fails, so each api is created
        once and then cached in __dict__.
        """
        canonical = self._API_ALIASES.get(name, name)
        class_name = self._API_CLASSES.get(canonical)
        if class_name is None:
            raise AttributeError(
                f"{type(self).__name__!r} object has no attribute {name!r}"
            )

        # __init__ must have run; guard against access on a half-built instance
        # (e.g. during unpickling) recursing back into __getattr__.
        if "api_client" not in self.__dict__:
            raise AttributeError(
                f"cannot build {canonical!r} before BelyApiFactory.__init__ has run"
            )

        import belyApi

        api = getattr(belyApi, class_name)(api_client=self.api_client)
        setattr(self, canonical, api)
        if name != canonical:
            setattr(self, name, api)
        return api

    def __dir__(self):
        return sorted(
            set(super().__dir__())
            | set(self._API_CLASSES)
            | set(self._API_ALIASES)
        )

    def _deprecated(self, old_name, new_name):
        warnings.warn(
            f"{old_name} is deprecated, use {new_name} instead",
            DeprecationWarning,
            stacklevel=3,
        )

    # -- snake_case methods (primary) --

    def get_logbook_api(self) -> LogbookApi:
        return self.logbook_api

    def get_domain_api(self) -> DomainApi:
        return self.domain_api

    def get_download_api(self) -> DownloadsApi:
        return self.downloads_api

    def get_property_value_api(self) -> PropertyValueApi:
        return self.property_value_api

    def get_users_api(self) -> UsersApi:
        return self.users_api

    def get_search_api(self) -> SearchApi:
        return self.search_api

    def get_notification_configuration_api(self):
        return self.notification_configuration_api

    def generate_cdb_url_for_item_id(self, item_id):
        return self.URL_FORMAT % (self.bely_url, str(item_id))

    def authenticate_user(self, username, password):
        response = self.auth_api.authenticate_user_with_http_info(
            username=username, password=password
        )

        token = response.headers[self.HEADER_TOKEN_KEY]
        self.__set_authenticate_token(token)

    def __set_authenticate_token(self, token):
        self.api_client.set_default_header(self.HEADER_TOKEN_KEY, token)

    def get_authenticate_token(self):
        return self.api_client.default_headers[self.HEADER_TOKEN_KEY]

    def test_authenticated(self):
        self.auth_api.verify_authenticated()

    def logout_user(self):
        self.auth_api.log_out()

    def parse_api_exception(self, open_api_exception):
        from belyApi import ApiExceptionMessage

        response_type = ApiExceptionMessage.__name__
        open_api_exception.data = open_api_exception.body
        ex_obj = self.api_client.deserialize(open_api_exception, response_type)
        ex_obj.status = open_api_exception.status
        return ex_obj

    # -- Deprecated camelCase wrappers --

    def getDomainApi(self) -> DomainApi:
        self._deprecated("getDomainApi", "get_domain_api")
        return self.get_domain_api()

    def getDownloadApi(self) -> DownloadsApi:
        self._deprecated("getDownloadApi", "get_download_api")
        return self.get_download_api()

    def getPropertyValueApi(self) -> PropertyValueApi:
        self._deprecated("getPropertyValueApi", "get_property_value_api")
        return self.get_property_value_api()

    def getUsersApi(self) -> UsersApi:
        self._deprecated("getUsersApi", "get_users_api")
        return self.get_users_api()

    def getSearchApi(self) -> SearchApi:
        self._deprecated("getSearchApi", "get_search_api")
        return self.get_search_api()

    def getNotificationConfigurationApi(self):
        self._deprecated("getNotificationConfigurationApi", "get_notification_configuration_api")
        return self.get_notification_configuration_api()

    def generateCDBUrlForItemId(self, itemId):
        self._deprecated("generateCDBUrlForItemId", "generate_cdb_url_for_item_id")
        return self.generate_cdb_url_for_item_id(itemId)

    def getAuthenticateToken(self):
        self._deprecated("getAuthenticateToken", "get_authenticate_token")
        return self.get_authenticate_token()

    def parseApiException(self, openApiException):
        self._deprecated("parseApiException", "parse_api_exception")
        return self.parse_api_exception(openApiException)

    # Restore later
    # @classmethod
    # def createFileUploadObject(cls, filePath):
    # 	data = open(filePath, "rb").read()
    # 	b64String = base64.b64encode(data).decode()

    # 	fileName = os.path.basename(filePath)
    # 	return FileUploadObject(file_name=fileName, base64_binary=b64String)


# def run_command():
# Example
# 	print("\nEnter cdb URL (ex: https://cdb.aps.anl.gov/cdb): ")
# 	hostname = input()

# 	apiFactory = CdbApiFactory(hostname)
# 	itemApi = apiFactory.getItemApi()

# 	catalogItems = itemApi.get_catalog_items()
# 	catalogItem = catalogItems[0]

# 	# Lists of items seem to be lists of dict items
# 	catalogId = catalogItem.id

# 	# Single items seem to be appropriate type
# 	catalogFetchedById = itemApi.get_item_by_id(catalogId)
# 	print(catalogFetchedById.name)

# 	inventoryItemPerCatalog = itemApi.get_items_derived_from_item_by_item_id(catalogId)
# 	print(inventoryItemPerCatalog)

# 	print("\n\n\nWould you like to test authentication? (y/N): ")
# 	resp = input()
# 	if resp == 'y' or resp == "Y":
# 		import getpass
# 		print("Username: ")
# 		username = input()
# 		print("Password: ")
# 		password = getpass.getpass()

# 		try:
# 			apiFactory.authenticateUser(username, password)
# 			apiFactory.testAuthenticated()
# 			apiFactory.logOutUser()
# 		except ApiException:
# 			print("Authentication failed!")
# 			exit(1)

# 		print("Success!")

if __name__ == "__main__":
    pass
# 	run_command()
