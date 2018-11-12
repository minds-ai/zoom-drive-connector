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
import tempfile
import os
import configuration

# pylint: disable=relative-beyond-top-level
from unittest_settings import TestSettingsBase


class TestBaseClass(unittest.TestCase):
  # pylint: disable=invalid-name
  def setUp(self):
    self.config = {'hello': 'world', 'inner': {'value': 2}, 'exlist': [1, 2], 'exbool': True}
    self.base = configuration.APIConfigBase(self.config)

  def test_validation(self):
    self.assertTrue(self.base.validate())

  def test_getattr(self):
    self.assertEqual(self.base.hello, 'world')
    self.assertEqual(self.base.inner, {'value': 2})
    self.assertEqual(self.base.exlist, [1, 2])
    self.assertTrue(self.base.exbool)

    with self.assertRaises(KeyError):
      # pylint: disable=unused-variable
      test_value = self.base.test

    with self.assertRaises(KeyError):
      # pylint: disable=unused-variable
      test_value = self.base.test.inner


class TestSlackConfig(TestSettingsBase):
  # pylint: disable=invalid-name
  def setUp(self):
    super(TestSlackConfig, self).setUp()
    self.slack = configuration.SlackConfig(self.slack_config)

  def test_validation(self):
    self.assertTrue(self.slack.validate())

  def test_getattr(self):
    self.assertEqual(self.slack.channel_name, 'some_channel')
    with self.assertRaises(KeyError):
      # pylint: disable=unused-variable
      test_value = self.slack.random_value

  def test_registrar(self):
    self.assertTrue(configuration.SlackConfig.factory_registrar('slack'))
    self.assertFalse(configuration.SlackConfig.factory_registrar('zoom'))


class TestZoomConfig(TestSettingsBase):
  # pylint: disable=invalid-name
  def setUp(self):
    super(TestZoomConfig, self).setUp()
    self.zoom = configuration.ZoomConfig(self.zoom_config)

  def test_validation(self):
    self.assertTrue(self.zoom.validate())

  def test_getattr(self):
    self.assertEqual(self.zoom.key, 'some_key')
    self.assertEqual(self.zoom.username, 'some@email.com')
    self.assertEqual(self.zoom.password, 's0mer4ndomv4lue!')
    self.assertTrue(self.zoom.delete)
    self.assertEqual(self.zoom.meetings,
                     [{'id': 'first_id', 'name': 'meeting1'},
                      {'id': 'second_id', 'name': 'meeting2'}]
                     )

    with self.assertRaises(KeyError):
      # pylint: disable=unused-variable
      test_value = self.zoom.random_value

  def test_registrar(self):
    self.assertTrue(configuration.ZoomConfig.factory_registrar('zoom'))
    self.assertFalse(configuration.ZoomConfig.factory_registrar('drive'))


class TestDriveConfig(TestSettingsBase):
  # pylint: disable=invalid-name
  def setUp(self):
    super(TestDriveConfig, self).setUp()
    self.drive = configuration.DriveConfig(self.drive_config)

    # Create temporary configuration file for validation testing.
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
      self.secrets_file_name = f.name

    self.drive_config['client_secret_json'] = self.secrets_file_name

  def tearDown(self):
    # Remove temporary configuration file.
    os.remove(self.secrets_file_name)

  def test_validation(self):
    self.assertTrue(self.drive.validate())

  def test_getattr(self):
    self.assertEqual(self.drive.credentials_json, '/tmp/credentials.json')

    with self.assertRaises(KeyError):
      # pylint: disable=unused-variable
      test_value = self.drive.not_here

  def test_registrar(self):
    self.assertTrue(configuration.DriveConfig.factory_registrar('drive'))
    self.assertFalse(configuration.DriveConfig.factory_registrar('random'))


class TestInternalConfig(TestSettingsBase):
  # pylint: disable=invalid-name
  def setUp(self):
    super(TestInternalConfig, self).setUp()
    self.internal = configuration.SystemConfig(self.internal_config)

  def test_validation(self):
    self.assertTrue(self.internal.validate())

  def test_getattr(self):
    self.assertEqual(self.internal.target_folder, os.getenv('TMPDIR', '/tmp'))

    with self.assertRaises(KeyError):
      # pylint: disable=unused-variable
      test_value = self.internal.random_value

  def test_registrar(self):
    self.assertTrue(configuration.SystemConfig.factory_registrar('internals'))
    self.assertFalse(configuration.SystemConfig.factory_registrar('not_working'))


class TestConfigInterface(unittest.TestCase):
  # pylint: disable=invalid-name
  def setUp(self):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
      self.secrets_file_name = f.name

    config_document = (
      'zoom:\n'
      '  key: "zoom_api_key"\n'
      '  secret: "zoom_api_secret"\n'
      '  username: "email@example.com"\n'
      '  password: "password for email@example.com"\n'
      '  delete: true\n'
      '  meetings:\n'
      '    - {id: "meeting_id" , name: "Meeting Name"}\n'
      '    - {id: "meeting_id2" , name: "Second Meeting Name"}\n'
      'drive:\n'
      '  credentials_json: "/tmp/credentials.json"\n'
      f'  client_secret_json: "{self.secrets_file_name}"\n'
      '  folder_id: "Some Google Drive Folder ID"\n'
      'slack:\n'
      '  channel: "channel_name"\n'
      '  key: "slack_api_key"\n'
      'internals:\n'
      '  target_folder: /tmp'
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as f:
      enc_doc = config_document.encode('utf-8')
      f.write(bytes(enc_doc))

      self.config_file_name = f.name

    self.interface = configuration.ConfigInterface(self.config_file_name)

  def tearDown(self):
    # Remove temporary configuration file.
    os.remove(self.config_file_name)
    os.remove(self.secrets_file_name)

  def test_nested_getattr(self):
    zoom = self.interface.zoom
    self.assertEqual(zoom.username, 'email@example.com')

    with self.assertRaises(KeyError):
      # pylint: disable=unused-variable
      test_value = zoom.email

  def test_getattr(self):
    self.assertIsInstance(self.interface.drive, configuration.DriveConfig)
    self.assertIsInstance(self.interface.zoom, configuration.ZoomConfig)
    self.assertIsInstance(self.interface.slack, configuration.SlackConfig)
    self.assertIsInstance(self.interface.internals, configuration.SystemConfig)
