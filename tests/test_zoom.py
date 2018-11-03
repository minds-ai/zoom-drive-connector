import unittest
import datetime
import responses
import zoom
import time
import jwt

from configuration import ZoomConfig, SystemConfig

class TestZoom(unittest.TestCase):
  sys_config = SystemConfig({'target_folder': '/tmp'})
  zoom_config = ZoomConfig({'key': 'some_key',
                            'secret': 'some_secret',
                            'username': 'some@email.com',
                            'password': 's0mer4ndomv4lue!',
                            'delete': True,
                            'meetings': [
                              {'id': 'first_id', 'name': 'meeting1'},
                              {'id': 'second_id', 'name': 'meeting2'}
                            ]})
  api = zoom.ZoomAPI(zoom_config, sys_config)

  def test_generate_jwt(self):
    token = jwt.encode({'iss': self.zoom_config.key, 'exp': int(time.time() + 1800)},
                       str(self.zoom_config.secret),
                       algorithm='HS256')

    self.assertEqual(self.api.generate_jwt(), token)

  @responses.activate
  def test_get_url_success(self):
    responses.add(responses.GET, 'https://api.zoom.us/v2/meetings/some-meeting-id/recordings',
                  status=200,
                  json={'recording_files': [{
                    'file_type': 'MP4',
                    'recording_start': '2018-01-01T01:01:01Z',
                    'download_url': 'https://example.com/download',
                    'id': 'some-recording-id'
                  }]})

    self.assertEqual(self.api.get_recording_url('some-meeting-id', b'token'),
                     {'date': datetime.datetime(2018, 1, 1, 1, 1, 1),
                       'id': 'some-recording-id',
                       'url': 'https://example.com/download'}
                     )

  @responses.activate
  def test_get_recording_url_fail(self):
    responses.add(responses.GET, 'https://api.zoom.us/v2/meetings/some-meeting-id/recordings',
                  status=404)

    with self.assertRaises(zoom.ZoomAPIException):
      self.api.get_recording_url('some-meeting-id', b'token')

    responses.add(responses.GET, 'https://api.zoom.us/v2/meetings/some-meeting-id/recordings',
                  status=300)

    with self.assertRaises(zoom.ZoomAPIException):
      self.api.get_recording_url('some-meeting-id', b'token')

    responses.add(responses.GET, 'https://api.zoom.us/v2/meetings/some-meeting-id/recordings',
                  status=500)

    with self.assertRaises(zoom.ZoomAPIException):
      self.api.get_recording_url('some-meeting-id', b'token')
