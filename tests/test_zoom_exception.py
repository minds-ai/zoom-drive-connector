import unittest

from requests import PreparedRequest
from zoom import ZoomAPIException

class TestZoomAPIException(unittest.TestCase):
  def test_throw_exception(self):
    with self.assertRaises(ZoomAPIException):
      raise ZoomAPIException(0, 'Test', None, 'Test message')

  def test_str_method(self):
    self.assertEqual(str(ZoomAPIException(404, 'Not found', None, 'File not found.')),
                     'HTTP_STATUS: 404-Not found, File not found.')

  def test_repr(self):
    self.assertEqual(repr(ZoomAPIException(0, 'Test', None, 'Test message')), 'ZoomAPIException()')

  def test_http_method(self):
    unknown_method = ZoomAPIException(0, 'Test', None, 'Test message')
    self.assertEqual(unknown_method.http_method, None)

    req = PreparedRequest()
    req.prepare_method('GET')
    known_method = ZoomAPIException(0, 'Test', req, 'Message')

    self.assertEqual(known_method.http_method, 'GET')
