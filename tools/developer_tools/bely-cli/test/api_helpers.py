"""Generated-client-aware test doubles for API-facing tests."""

import inspect
from unittest.mock import create_autospec

from BelyApiFactory import BelyApiFactory
from belyApi.api.downloads_api import DownloadsApi
from belyApi.api.logbook_api import LogbookApi
from belyApi.api.search_api import SearchApi
from belyApi.api.users_api import UsersApi


def api_mock(api_type=LogbookApi):
    """Return a mock that rejects methods and arguments absent from the generated API."""
    return create_autospec(api_type, instance=True, spec_set=True)


def method_mock(api_type, method, **kwargs):
    """Mock one generated API method while preserving its call signature."""
    mocked_method = getattr(api_mock(api_type), method)
    wraps = kwargs.pop("wraps", None)
    mocked_method.configure_mock(**kwargs)
    if wraps is not None:
        mocked_method.side_effect = wraps
    return mocked_method


def factory_mock():
    """Return a mock constrained to the API factory shipped with bely-api."""
    return create_autospec(BelyApiFactory, instance=True, spec_set=True)


def api_fake(api_type):
    """Validate that a hand-written fake only implements generated API methods."""
    def validate(fake_type):
        for base in fake_type.__mro__:
            if base is object:
                continue
            for name, value in base.__dict__.items():
                if name.startswith("_") or name == "__init__" or not callable(value):
                    continue
                if not hasattr(api_type, name):
                    raise TypeError(
                        f"{fake_type.__name__}.{name} is not part of {api_type.__name__}"
                    )
                generated_params = set(inspect.signature(getattr(api_type, name)).parameters)
                fake_params = set(inspect.signature(value).parameters)
                unknown = fake_params - generated_params
                if unknown:
                    raise TypeError(
                        f"{fake_type.__name__}.{name} has unsupported parameters: "
                        f"{', '.join(sorted(unknown))}"
                    )
        return fake_type

    return validate
