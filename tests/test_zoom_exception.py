# Copyright 2018 Minds.ai, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import unittest

from requests import PreparedRequest
from zoom_drive_connector.zoom import ZoomAPIException


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
