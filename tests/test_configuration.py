import unittest
import os
import configuration

slack_config = {'channel_name': 'some_channel', 'key': 'random_key'}
zoom_config = {'key': 'some_key',
               'secret': 'some_secret',
               'username': 'some@email.com',
               'password': 's0mer4ndomv4lue!',
               'delete': True,
               'meetings': [
                 {'id': 'first_id', 'name': 'meeting1'},
                 {'id': 'second_id', 'name': 'meeting2'}
               ]}
drive_config = {'credentials_json': '/tmp/credentials.json',
                'client_secret_json': '/tmp/client_secrets.json',
                'folder_id': 'some_id'}
internal_config = {'target_folder': '/tmp'}


def touch(path):
  with open(path, 'a'):
    os.utime(path, None)


class TestBaseClass(unittest.TestCase):
  config = {'hello': 'world', 'inner': {'value': 2}, 'exlist': [1, 2], 'exbool': True}
  base = configuration.APIConfigBase(config)

  def test_validation(self):
    self.assertTrue(self.base.validate())

  def test_getattr(self):
    self.assertEqual(self.base.hello, 'world')
    self.assertEqual(self.base.inner, {'value': 2})
    self.assertEqual(self.base.exlist, [1, 2])
    self.assertTrue(self.base.exbool)

    with self.assertRaises(KeyError):
      # pylint: disable=W0612
      test_value = self.base.test

    with self.assertRaises(KeyError):
      # pylint: disable=W0612
      test_value = self.base.test.inner


class TestSlackConfig(unittest.TestCase):
  slack = configuration.SlackConfig(slack_config)

  def test_validation(self):
    self.assertTrue(self.slack.validate())

  def test_getattr(self):
    self.assertEqual(self.slack.channel_name, 'some_channel')
    with self.assertRaises(KeyError):
      # pylint: disable=W0612
      test_value = self.slack.random_value

  def test_registrar(self):
    self.assertTrue(configuration.SlackConfig.factory_registrar('slack'))
    self.assertFalse(configuration.SlackConfig.factory_registrar('zoom'))


class TestZoomConfig(unittest.TestCase):
  zoom = configuration.ZoomConfig(zoom_config)

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
      # pylint: disable=W0612
      test_value = self.zoom.random_value

  def test_registrar(self):
    self.assertTrue(configuration.ZoomConfig.factory_registrar('zoom'))
    self.assertFalse(configuration.ZoomConfig.factory_registrar('drive'))


class TestDriveConfig(unittest.TestCase):
  drive = configuration.DriveConfig(drive_config)

  def test_validation(self):
    touch('/tmp/client_secrets.json')
    self.assertTrue(self.drive.validate())

    os.remove('/tmp/client_secrets.json')

  def test_getattr(self):
    self.assertEqual(self.drive.credentials_json, '/tmp/credentials.json')

    with self.assertRaises(KeyError):
      # pylint: disable=W0612
      test_value = self.drive.not_here

  def test_registrar(self):
    self.assertTrue(configuration.DriveConfig.factory_registrar('drive'))
    self.assertFalse(configuration.DriveConfig.factory_registrar('random'))


class TestInternalConfig(unittest.TestCase):
  internal = configuration.SystemConfig(internal_config)

  def test_validation(self):
    self.assertTrue(self.internal.validate())

  def test_getattr(self):
    self.assertEqual(self.internal.target_folder, '/tmp')

    with self.assertRaises(KeyError):
      # pylint: disable=W0612
      test_value = self.internal.random_value

  def test_registrar(self):
    self.assertTrue(configuration.SystemConfig.factory_registrar('internals'))
    self.assertFalse(configuration.SystemConfig.factory_registrar('not_working'))


class TestConfigInterface(unittest.TestCase):
  touch('/tmp/client_secrets.json')
  interface = configuration.ConfigInterface(os.getcwd() + '/tests/test.yaml')
  os.remove('/tmp/client_secrets.json')

  def test_nested_getattr(self):
    zoom = self.interface.zoom
    self.assertEqual(zoom.username, 'email@example.com')

    with self.assertRaises(KeyError):
      # pylint: disable=W0612
      test_value = zoom.email

  def test_getattr(self):
    self.assertEqual(type(self.interface.drive), configuration.DriveConfig)
    self.assertEqual(type(self.interface.zoom), configuration.ZoomConfig)
    self.assertEqual(type(self.interface.slack), configuration.SlackConfig)
    self.assertEqual(type(self.interface.internals), configuration.SystemConfig)
