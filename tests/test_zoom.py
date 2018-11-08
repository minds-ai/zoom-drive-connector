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

import datetime
import time

from unittest.mock import MagicMock

import responses
import zoom
import jwt

from configuration import ZoomConfig, SystemConfig

# pylint: disable=E0402
from unittest_settings import TestSettingsBase


class TestZoom(TestSettingsBase):
  def setUp(self):
    super(TestZoom, self).setUp()

    self.zoom_object = ZoomConfig(self.zoom_config)
    self.sys_object = SystemConfig(self.internal_config)

    self.api = zoom.ZoomAPI(self.zoom_object, self.sys_object)

  def test_generate_jwt_valid_token(self):
    token = jwt.encode({'iss': self.zoom_object.key, 'exp': int(time.time() + 1800)},
                       str(self.zoom_object.secret),
                       algorithm='HS256')

    self.assertEqual(self.api.generate_jwt(), token)

  def test_generate_jwt_invalid_token(self):
    token = jwt.encode({'iss': 'fake', 'exp': int(time.time())},
                       str(self.zoom_object.secret),
                       algorithm='HS256')

    self.assertNotEqual(self.api.generate_jwt(), token)

  @responses.activate
  def test_delete_recording_errors(self):
    responses.add(responses.DELETE, 'https://api.zoom.us/v2/meetings/some-meeting/recordings/rid',
                  status=404)

    with self.assertRaises(zoom.ZoomAPIException):
      self.api.delete_recording('some-meeting', 'rid', b'token')

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

  @responses.activate
  def test_downloading_file(self):
    pass
    # TODO: Not really sure how to test a streaming file download.
    # TODO(nick): This method needs to have more rigorous exception checking.

  @responses.activate
  def test_handling_zoom_errors_file_pull(self):
    responses.add(responses.GET, 'https://api.zoom.us/v2/meetings/some-meeting-id/recordings',
                  status=404)

    self.assertEqual(self.api.pull_file_from_zoom('some-meeting-id', True),
                     {'success': False, 'date': None, 'filename': None})

    # TODO: handle calling delete method. However, this relies on previous test being completed.

  @responses.activate
  def test_filesystem_errors_file_pull(self):
    responses.add(responses.GET, 'https://api.zoom.us/v2/meetings/some-meeting-id/recordings',
                  status=200,
                  json={'recording_files': [{
                    'file_type': 'MP4',
                    'recording_start': '2018-01-01T01:01:01Z',
                    'download_url': 'https://example.com/download',
                    'id': 'some-recording-id'
                  }]})

    self.api.download_recording = MagicMock(side_effect=OSError('Could not write file!'))
    self.assertEqual(self.api.pull_file_from_zoom('some-meeting-id', True),
                     {'success': False, 'date': None, 'filename': None})
