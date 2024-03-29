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
import shutil
import logging
from typing import TypeVar, cast, Dict, Any

import requests
from requests.auth import HTTPBasicAuth

from zoom_drive_connector.configuration import APIConfigBase, ZoomConfig, SystemConfig

from .zoom_api_exception import ZoomAPIException

log = logging.getLogger('app')
S = TypeVar("S", bound=APIConfigBase)


class ZoomURLS(Enum):
  recordings = 'https://api.zoom.us/v2/meetings/{id}/recordings'
  zak_token = 'https://api.zoom.us/v2/users/{user}/token?type=zak'
  delete_recordings = 'https://api.zoom.us/v2/meetings/{id}/recordings/{rid}'
  signin = 'https://api.zoom.us/signin'
  oauth_token = 'https://zoom.us/oauth/token'


class ZoomAPI:
  def __init__(self, zoom_config: S, sys_config: S):
    """Class initialization; sets client key, secret, and download folder path.

    :param zoom_config: configuration class containing all relevant parameters for Zoom API.
    :param sys_config: configuration class containing target folder where to download contains.
    """
    self.zoom_config = cast(ZoomConfig, zoom_config)
    self.sys_config = cast(SystemConfig, sys_config)

    self.timeout = 1800  # Default expiration time is 30 minutes.

    # Clarified HTTP status messages
    self.message = {
        401: 'Not authenticated.',
        404: 'File not found or no recordings',
        409: 'File deleted already.'
    }

  def generate_server_to_server_oath_token(self) -> bytes:
    """Generates the OATH token used for authenticating with Zoom.

    Sends OATH information and receives a token to use for the next hour.
    """
    data = {
      "grant_type" : "account_credentials",
      "account_id" : self.zoom_config.account_id
    }
    headers = {
     'content-type': 'application/x-www-form-urlencoded'
    }
    res = requests.post(
      ZoomURLS.oauth_token.value,
      headers=headers,
      params=data,
      auth=HTTPBasicAuth(self.zoom_config.client_id, self.zoom_config.client_secret)
    )
    if res.status_code != 200:
      raise ValueError("Failed to authenticate, error: ", res.json())
    return res.json()["access_token"]

  def delete_recording(self, meeting_id: str, recording_id: str, auth: bytes):
    """Given a specific meeting room ID and recording ID, this function moves the recording to the
    trash in Zoom's cloud.

    :param meeting_id: UUID associated with a meeting room.
    :param recording_id: The ID of the recording to trash.
    :param auth: OAUTH token.
    """
    zoom_url = str(ZoomURLS.delete_recordings.value).format(id=meeting_id, rid=recording_id)
    headers = {
      'authorization': 'Bearer ' + auth,
      'content-type': 'application/json'
    }
    # trash, not delete
    res = requests.delete(zoom_url, headers=headers, params={'action': 'trash'})
    status_code = res.status_code
    if 400 <= status_code <= 499:
      raise ZoomAPIException(status_code, res.reason, res.request, self.message.get(
          status_code, ''))

  def get_recording_url(self, meeting_id: str, auth: str) -> Dict[str, Any]:
    """Given a specific meeting room ID and auth token, this function gets the download url
    for most recent recording in the given meeting room.

    :param meeting_id: UUID associated with a meeting room.
    :param auth: Authorization token
    :return: dict containing the date of the recording, the ID of the recording, and the video url.
    """
    zoom_url = str(ZoomURLS.recordings.value).format(id=meeting_id)

    try:
      headers = {
        'authorization': 'Bearer ' + auth,
        'content-type': 'application/json'
      }
      zoom_request = requests.get(zoom_url, headers=headers)
    except requests.exceptions.RequestException as e:
      # Failed to make a connection so let's just return a 404, as there is no file
      # but print an additional warning in case it was a configuration error
      log.log(logging.ERROR, e)
      raise ZoomAPIException(404, 'File Not Found', None, 'Could not connect')

    status_code = zoom_request.status_code
    if 200 <= status_code <= 299:
      log.log(logging.DEBUG, zoom_request.json())
      for req in zoom_request.json()['recording_files']:
        # TODO(jbedorf): For now just delete the chat messages and continue processing other files.
        if req['file_type'] == 'CHAT':
          self.delete_recording(req['meeting_id'], req['id'], auth)
        elif req['file_type'] == 'TRANSCRIPT':
          self.delete_recording(req['meeting_id'], req['id'], auth)
        elif req['file_type'] == 'MP4':
          date = datetime.datetime.strptime(req['recording_start'], '%Y-%m-%dT%H:%M:%SZ')
          return {
            'date': date,
            'id': req['id'],
            'url': req['download_url'],
            'meeting_id': req['meeting_id']
          }
      # Raise 404 when we do not recognize the file type.
      raise ZoomAPIException(404, 'File Not Found', zoom_request.request, # pylint: no-else-raise
                             'File not found or no recordings')
    elif 300 <= status_code <= 599:
      raise ZoomAPIException(status_code, zoom_request.reason, zoom_request.request,
                             self.message.get(status_code, ''))
    else:
      raise ZoomAPIException(status_code, zoom_request.reason, zoom_request.request, '')

  def download_recording(self, url: str, auth: str) -> str:
    """Downloads video file from Zoom to local folder.

    :param url: Download URL for meeting recording.
    :param auth: Authorization token.
    :return: Path to the recording
    """
    headers = {
      'authorization': 'Bearer ' + auth,
      'content-type': 'application/json'
    }
    zoom_request = requests.get(url, stream=True, headers=headers)

    filename = url.split('/')[-1]
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
      log.log(logging.INFO, f'Found recording for meeting {meeting_id} starting download...')
      # Generate token and Authorization header.
      zoom_token = self.generate_server_to_server_oath_token()

      # Get URL and download the file.
      res = self.get_recording_url(meeting_id, zoom_token)
      filename = self.download_recording(res['url'], zoom_token)

      if rm:
        self.delete_recording(res['meeting_id'], res['id'], zoom_token)
      log.log(logging.INFO, f'File {filename} downloaded for meeting {meeting_id}.')
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
