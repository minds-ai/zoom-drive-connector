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
from enum import Enum
import os
import time
import shutil
import logging
from typing import TypeVar, cast, Dict, Any

import requests
import jwt

from zoom import ZoomAPIException
from configuration import APIConfigBase, ZoomConfig, SystemConfig

log = logging.getLogger('app')
S = TypeVar("S", bound=APIConfigBase)


class ZoomURLS(Enum):
  recordings = 'https://api.zoom.us/v2/meetings/{id}/recordings'
  delete_recordings = 'https://api.zoom.us/v2/meetings/{id}/recordings/{rid}'
  signin = 'https://api.zoom.us/signin'


class ZoomAPI:
  def __init__(self, zoom_config: S, sys_config: S):
    """Class initialization; sets client key, secret, and download folder path.

    :param zoom_config: configuration class containing all relevant parameters for Zoom API.
    :param sys_config: configuration class containing target folder where to download contains.
    """
    self.zoom_config = cast(ZoomConfig, zoom_config)
    self.sys_config = cast(SystemConfig, sys_config)

    # Information required to login to allow downloads
    self.zoom_signin_url = ZoomURLS.signin.value
    self.timeout = 1800  # Default expiration time is 30 minutes.

    # Clarified HTTP status messages
    self.message = {
        401: 'Not authenticated.',
        404: 'File not found or no recordings',
        409: 'File deleted already.'
    }

  def generate_jwt(self) -> bytes:
    """Generates the JSON web token used for authenticating with Zoom. Sends client key
    and expiration time encoded with the secret key.
    """
    payload = {'iss': self.zoom_config.key, 'exp': int(time.time()) + self.timeout}
    return jwt.encode(payload, str(self.zoom_config.secret), algorithm='HS256')

  def delete_recording(self, meeting_id: str, recording_id: str, auth: bytes):
    """Given a specific meeting room ID and recording ID, this function moves the recording to the
    trash in Zoom's cloud.

    :param meeting_id: UUID associated with a meeting room.
    :param recording_id: The ID of the recording to trash.
    :param auth: JWT token.
    """
    zoom_url = str(ZoomURLS.delete_recordings.value).format(id=meeting_id, rid=recording_id)
    res = requests.delete(
        zoom_url, params={'access_token': auth,
                          'action': 'trash'})  # trash, not delete
    status_code = res.status_code
    if 400 <= status_code <= 499:
      raise ZoomAPIException(status_code, res.reason, res.request, self.message.get(
          status_code, ''))

  def get_recording_url(self, meeting_id: str, auth: bytes) -> Dict[str, Any]:
    """Given a specific meeting room ID and auth token, this function gets the download url
    for most recent recording in the given meeting room.

    :param meeting_id: UUID associated with a meeting room.
    :param auth: Encoded JWT authorization token
    :return: dict containing the date of the recording, the ID of the recording, and the video url.
    """
    zoom_url = str(ZoomURLS.recordings.value).format(id=meeting_id)

    try:
      zoom_request = requests.get(zoom_url, params={'access_token': auth})
    except requests.exceptions.RequestException as e:
      # Failed to make a connection so let's just return a 404, as there is no file
      # but print an additional warning in case it was a configuration error
      log.log(logging.ERROR, e)
      raise ZoomAPIException(404, 'File Not Found', None, 'Could not connect')

    status_code = zoom_request.status_code
    if 200 <= status_code <= 299:
      for req in zoom_request.json()['recording_files']:
        # TODO(jbedorf): For now just delete the chat messages and continue processing other files.
        if req['file_type'] == 'CHAT':
          self.delete_recording(meeting_id, req['id'], auth)
        elif req['file_type'] == 'MP4':
          date = datetime.datetime.strptime(req['recording_start'], '%Y-%m-%dT%H:%M:%SZ')
          return {'date': date, 'id': req['id'], 'url': req['download_url']}
      # Raise 404 when we do not recognize the file type
      raise ZoomAPIException(404, 'File Not Found', zoom_request.request,
                             'File not found or no recordings')
    elif 300 <= status_code <= 599:
      raise ZoomAPIException(status_code, zoom_request.reason, zoom_request.request,
                             self.message.get(status_code, ''))
    else:
      raise ZoomAPIException(status_code, zoom_request.reason, zoom_request.request, '')

  def download_recording(self, url: str) -> str:
    """Downloads video file from Zoom to local folder.

    :param url: Download URL for meeting recording.
    :return: Path to the recording
    """
    session = requests.Session()
    session.headers.update({'content-type': 'application/x-www-form-urlencoded'})

    session.post(
        self.zoom_signin_url,
        data={'email': str(self.zoom_config.username),
              'password': str(self.zoom_config.password)})

    filename = url.split('/')[-1]
    zoom_request = session.get(url, stream=True)

    outfile = os.path.join(str(self.sys_config.target_folder), filename + '.mp4')
    with open(outfile, 'wb') as source:
      shutil.copyfileobj(zoom_request.raw, source)  # Copy raw file data to local file.
    return outfile

  def pull_file_from_zoom(self, meeting_id: str, rm: bool = True) -> Dict[str, Any]:
    """Interface for downloading recordings from Zoom. Optionally trashes recorded file on Zoom.
    Returns a dictionary containing success state and/or recording information.

    :param meeting_id: UUID for meeting room where recording was just completed.
    :param rm: If true is passed (default) then file is trashed on Zoom.
    :return: dict containing if the operation was successful. If downloading and (optionally)
      deleting the recording on Zoom completed successfully, include the recording date and the
      recording filename.
    """
    result = {'success': False, 'date': None, 'filename': None}
    try:
      # Generate token and Authorization header.
      zoom_token = self.generate_jwt()

      # Get URL and download the file.
      res = self.get_recording_url(meeting_id, zoom_token)
      filename = self.download_recording(res['url'])

      if rm:
        self.delete_recording(meeting_id, res['id'], zoom_token)
      log.log(logging.INFO, 'File {} downloaded for meeting {}.'.format(filename, meeting_id))
      return {'success': True, 'date': res['date'], 'filename': filename}
    except ZoomAPIException as ze:
      if ze.http_method and ze.http_method == 'DELETE':
        log.log(logging.INFO, ze)
        # Allow other systems to proceed if delete fails.
        result['success'] = True
        return result
      log.log(logging.ERROR, ze)
      return result
    except OSError as fe:
      # Catches general filesystem errors. If download could not be written to disk, stop.
      log.log(logging.ERROR, fe)
      return result
