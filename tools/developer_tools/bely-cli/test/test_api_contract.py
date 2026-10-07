"""Release contract between bely-cli and the generated bely-api package."""

import inspect

import pytest

from BelyApiFactory import BelyApiFactory
from belyApi.api.downloads_api import DownloadsApi
from belyApi.api.logbook_api import LogbookApi
from belyApi.api.search_api import SearchApi
from belyApi.api.users_api import UsersApi


API_METHODS = {
    LogbookApi: {
        "add_update_log_entry",
        "create_logbook_document",
        "delete_attachment",
        "delete_log_document",
        "delete_log_entry",
        "get_log_document_by_name",
        "get_log_documents",
        "get_log_entries",
        "get_log_entry_attachments",
        "get_log_entry_template",
        "get_logbook_systems",
        "get_logbook_templates",
        "get_logbook_type_hierarchy",
        "get_logbook_types",
        "upload_attachment",
    },
    DownloadsApi: {
        "get_attachment1_without_preload_content",
        "get_attachment_without_preload_content",
    },
    SearchApi: {"search_logbook"},
    UsersApi: {"get_user_by_username"},
    BelyApiFactory: {
        "authenticate_user",
        "get_authenticate_token",
        "get_download_api",
        "get_logbook_api",
        "get_search_api",
        "get_users_api",
        "logout_user",
        "parse_api_exception",
        "test_authenticated",
    },
}


@pytest.mark.parametrize(
    ("api_type", "method"),
    [
        (api_type, method)
        for api_type, methods in API_METHODS.items()
        for method in sorted(methods)
    ],
)
def test_required_api_method_exists(api_type, method):
    assert callable(getattr(api_type, method, None)), (
        f"{api_type.__name__}.{method} is required by bely-cli but missing from bely-api"
    )


@pytest.mark.parametrize(
    ("method", "parameters"),
    [
        ("delete_log_document", {"log_document_id"}),
        ("delete_log_entry", {"log_document_id", "log_id"}),
        ("delete_attachment", {"log_document_id", "log_id", "attachment_id"}),
    ],
)
def test_delete_api_signatures(method, parameters):
    signature = inspect.signature(getattr(LogbookApi, method))
    assert parameters <= set(signature.parameters)
