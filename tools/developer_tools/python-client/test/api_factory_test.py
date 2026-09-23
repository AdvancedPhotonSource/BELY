import json
import unittest
from types import SimpleNamespace

from BelyApiFactory import BelyApiFactory


class ParseApiExceptionTests(unittest.TestCase):
    def _factory_without_client(self):
        return object.__new__(BelyApiFactory)

    def test_parses_real_server_response_body(self):
        payload = {
            "simpleName": "ObjectNotFound",
            "message": "Could not find item with id: 90099",
            "exception": {
                "cause": None,
                "stackTrace": [{
                    "classLoaderName": None,
                    "moduleName": None,
                    "moduleVersion": None,
                    "methodName": "getItemByIdBase",
                    "fileName": "ItemBaseRoute.java",
                    "lineNumber": 30,
                    "className": "gov.anl.aps.logr.rest.routes.ItemBaseRoute",
                    "nativeMethod": False,
                }],
                "message": "Could not find item with id: 90099",
                "suppressed": [],
                "localizedMessage": "Could not find item with id: 90099",
            },
        }
        error = SimpleNamespace(body=json.dumps(payload), data=None)

        parsed = self._factory_without_client().parse_api_exception(error)

        self.assertEqual(parsed.simple_name, "ObjectNotFound")
        self.assertEqual(parsed.message, "Could not find item with id: 90099")

    def test_null_message_falls_back_to_exception_type(self):
        error = SimpleNamespace(
            body=json.dumps({
                "simpleName": "NullPointerException",
                "message": None,
                "exception": {"message": None, "localizedMessage": None},
            }),
            data=None,
            reason="Internal Server Error",
        )
        parsed = self._factory_without_client().parse_api_exception(error)
        self.assertEqual(parsed.message, "NullPointerException")

    def test_nested_exception_message_precedes_type(self):
        error = SimpleNamespace(
            body=json.dumps({
                "simpleName": "Failure",
                "message": None,
                "exception": {"message": "Specific failure"},
            }),
            data=None,
            reason="Internal Server Error",
        )
        parsed = self._factory_without_client().parse_api_exception(error)
        self.assertEqual(parsed.message, "Specific failure")

    def test_accepts_bytes_body(self):
        error = SimpleNamespace(body=b'{"message":"Denied"}', data=None)
        parsed = self._factory_without_client().parse_api_exception(error)
        self.assertEqual(parsed.message, "Denied")

    def test_uses_data_when_body_is_missing(self):
        error = SimpleNamespace(body=None, data={"message": "Unavailable"})
        parsed = self._factory_without_client().parse_api_exception(error)
        self.assertEqual(parsed.message, "Unavailable")

    def test_rejects_non_object_payload(self):
        error = SimpleNamespace(body='["invalid"]', data=None)
        with self.assertRaisesRegex(ValueError, "JSON object"):
            self._factory_without_client().parse_api_exception(error)


if __name__ == "__main__":
    unittest.main()
