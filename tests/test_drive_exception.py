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

from zoom_drive_connector.drive import DriveAPIException


class TestDriveAPIException(unittest.TestCase):
  def test_throw_exception(self):
    with self.assertRaises(DriveAPIException):
      raise DriveAPIException('Test', 'Test reason')

  def test_str_method(self):
    self.assertEqual(str(DriveAPIException('Test', 'Test reason.')),
                     'DRIVE_API_FAILURE: Test, Test reason.')

  def test_repr_method(self):
    self.assertEqual(repr(DriveAPIException('Test', 'Test reason')), 'DriveAPIException()')
