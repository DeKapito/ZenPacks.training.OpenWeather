from Products.ZenTestCase.BaseTestCase import BaseTestCase

from ZenPacks.training.OpenWeather.util import camelCaseToSnake

stringsForConvert = [
    ("CamelCase", "camel_case"),
    ("Camel2Camel2Case", "camel2_camel2_case"),
    ("getHTTPResponseCode", "get_http_response_code"),
    ("HTTPResponseCodeXYZ", "http_response_code_xyz"),
]


class UtilTest(BaseTestCase):

    def testCamelCaseToSnake(self):
        for camelCase, result in stringsForConvert:
            self.assertEqual(camelCaseToSnake(camelCase), result)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(UtilTest))
    return suite
