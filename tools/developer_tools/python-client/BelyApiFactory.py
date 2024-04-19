#!/usr/bin/env python

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.
import base64
import os

from belyApi import Configuration, ApiClient
from belyApi import DomainApi, DownloadsApi, UsersApi, PropertyValueApi, SystemLogApi, SearchApi, AuthenticationApi, LogbookApi
from belyApi import ApiExceptionMessage

class BelyApiFactory:

	HEADER_TOKEN_KEY = "token"
	URL_FORMAT = "%s/views/item/view?id=%s"

	LOGBOOK_DOMAIN_ID = 1
	

	def __init__(self, bely_url):
		self.bely_url = bely_url
		self.config = Configuration(host=self.bely_url)
		self.api_client = ApiClient(configuration=self.config)

		self.logbook_api = LogbookApi(api_client=self.api_client)

		self.downloadsApi = DownloadsApi(api_client=self.api_client)		
		self.propertyValueApi = PropertyValueApi(api_client=self.api_client)
		self.usersApi = UsersApi(api_client=self.api_client)
		self.domainApi = DomainApi(api_client=self.api_client)
		
		self.systemlogApi = SystemLogApi(api_client=self.api_client)		
		self.searchApi = SearchApi(api_client=self.api_client)

		self.auth_api = AuthenticationApi(api_client=self.api_client)	

	def get_lobook_api(self) -> LogbookApi:
		return self.logbook_api

	def getDomainApi(self) -> DomainApi:
		return self.domainApi

	def getDownloadApi(self) -> DownloadsApi:
		return self.downloadsApi

	def getPropertyValueApi(self) -> PropertyValueApi:
		return self.propertyValueApi

	def getUsersApi(self) -> UsersApi:
		return self.usersApi

	def getSearchApi(self) -> SearchApi:
		return self.searchApi

	def generateCDBUrlForItemId(self, itemId):
		return self.URL_FORMAT % (self.cdbUrl, str(itemId))

	def authenticate_user(self, username, password):
		response = self.auth_api.authenticate_user_with_http_info(username=username, password=password)

		token = response[-1][self.HEADER_TOKEN_KEY]
		self.__set_authenticate_token(token)

	def __set_authenticate_token(self, token):
		self.api_client.set_default_header(self.HEADER_TOKEN_KEY, token)

	def getAuthenticateToken(self):
		return self.apiClient.default_headers[self.HEADER_TOKEN_KEY]

	def test_authenticated(self):
		self.auth_api.verify_authenticated()

	def logout_user(self):
		self.auth_api.log_out()

	# Restore later 
	# @classmethod
	# def createFileUploadObject(cls, filePath):
	# 	data = open(filePath, "rb").read()
	# 	b64String = base64.b64encode(data).decode()

	# 	fileName = os.path.basename(filePath)
	# 	return FileUploadObject(file_name=fileName, base64_binary=b64String)

	def parseApiException(self, openApiException):
		responseType = ApiExceptionMessage.__name__
		openApiException.data = openApiException.body
		exObj = self.apiClient.deserialize(openApiException, responseType)
		exObj.status = openApiException.status
		return exObj

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

# if __name__ == '__main__':
# 	run_command()
