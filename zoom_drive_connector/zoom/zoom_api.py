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
import hmac
import hashlib
import shutil
import logging
from typing import List, TypeVar, cast, Dict, Any

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




# Create a class to handle the Zoom Webhook
class ZoomWebhook:
    def __init__(self, token: str):
        self.secret_token = token

    def verify_headers(self, headers: Dict, body: str) -> bool:
        """Verify the headers of the request, to validate the request is from Zoom."""
        if "x-zm-signature" not in headers or "x-zm-request-timestamp" not in headers:
            print("Invalid Zoom Headers, missing items. Content: ")
            for key, value in headers.items():
                print(f"   {key} = {value}")
            return False

        timestamp = headers["x-zm-request-timestamp"]


        hash_to_verify = hmac.new(
            self.secret_token.encode("utf-8"),
            f"v0:{timestamp}:{body}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signature = f"v0={hash_to_verify}"
        return True
        return hmac.compare_digest(signature, req.headers["x-zm-signature"])

    def handle_validation_event(self, body: dict):
        """Handle the validation of the Zoom Webhook URL."""
        secret_token = self.secret_token.encode("utf-8")
        plain_token = body["payload"]["plainToken"]
        message = plain_token.encode("utf-8")
        hashed = hmac.new(secret_token, message, hashlib.sha256).digest()
        return {"plainToken": plain_token, "encryptedToken": hashed.hex()}




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
    log.log(logging.INFO, f'Deleting recording {recording_id} for meeting {meeting_id}...')
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
            'meeting_id': req['meeting_id'],
          }
      # Raise 404 when we do not recognize the file type.
      raise ZoomAPIException(404, 'File Not Found', zoom_request.request, # pylint: no-else-raise
                             'File not found or no recordings')
    elif 300 <= status_code <= 599:
      raise ZoomAPIException(status_code, zoom_request.reason, zoom_request.request,
                             self.message.get(status_code, ''))
    else:
      raise ZoomAPIException(status_code, zoom_request.reason, zoom_request.request, '')

  def download_recording(self, url: str, auth: str, filename: str="") -> str:
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

    filename = filename or url.split('/')[-1]
    outfile = os.path.join(str(self.sys_config.target_folder), filename + '.mp4')
    with open(outfile, 'wb') as source:
      shutil.copyfileobj(zoom_request.raw, source)  # Copy raw file data to local file.

    return outfile

  def download_webhook_recording(self, url: str, download_token: str, filename: str="") -> str:
    """Downloads video file from Zoom to local folder.

    :param url: Download URL for meeting recording.
    :param auth: Authorization token.
    :return: Path to the recording
    """
    url = f"{url}?access_token={download_token}"
    zoom_request = requests.get(url, stream=True)

    outfile = os.path.join(str(self.sys_config.target_folder), filename)
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


  def webhook_summary_message(self, zoom_body: Dict) -> Dict[str, Any]:
    log.info(f"Processing webhook for completed summary.")

    result = {'success': False, 'summary': None, 'slack_channel': None, 'meeting': None}

    meeting_id = zoom_body["payload"]["object"]["meeting_id"]


    meeting_config = next(
      (meeting for meeting in self.zoom_config.meetings if meeting['id'] == str(meeting_id)), None
    )
    if not meeting_config:
        log.log(logging.ERROR, f"Meeting {meeting_id} not found in configuration.")
        return result

    result["slack_channel"] = meeting_config["slack_channel"]
    result["meeting"] = meeting_config["name"]
    result["meeting_uuid"] = zoom_body["payload"]["object"]["meeting_uuid"]
    result["success"] = True

    info = zoom_body["payload"]["object"]

    result["summary"] = {
      "date": datetime.datetime.strptime(info["meeting_start_time"], '%Y-%m-%dT%H:%M:%SZ'),
      "title": info.get("summary_title", "Summary"),
      "overview": info.get("summary_overview", "No overview provided."),
      "details": info.get("summary_details", []),
      "next_steps": info.get("next_steps", []),
    }
    log.log(logging.INFO, f"Meeting {meeting_id} summary processed and returned.")
    return result


  def webhook_recording_complete(self, zoom_body: Dict, types_to_download: List) -> Dict[str, Any]:

    log.info(f"Processing webhook for completed recording.")

    result = {'success': False, 'date': [], 'filename': []}

    meeting_id = zoom_body["payload"]["object"]["id"]
    recording_files = zoom_body["payload"]["object"]["recording_files"]

    log.info(f"Meeting ID: {meeting_id}")

    meeting_config = next(
      (meeting for meeting in self.zoom_config.meetings if meeting['id'] == str(meeting_id)), None
    )
    if not meeting_config:
        log.log(logging.ERROR, f"Meeting {meeting_id} not found in configuration.")
        return result

    result["folder_id"] = meeting_config["folder_id"]
    result["slack_channel"] = meeting_config["slack_channel"]
    result["meeting"] = meeting_config["name"]
    result['meeting_uuid'] = zoom_body["payload"]["object"]["uuid"]

    meeting_config: Dict = None
    for meeting in self.zoom_config.meetings:
      if meeting['id'] == str(meeting_id):
        meeting_config = meeting
    if not meeting_config:
      log.log(logging.ERROR, f"Meeting {meeting_id} not found in configuration.")
      return result


    try:
      log.log(logging.INFO, f'Recording triggered for meeting {meeting_id} starting download...')
      # Generate token and Authorization header.
      zoom_token = self.generate_server_to_server_oath_token()

      for file_info in recording_files:
        if file_info["file_type"].upper() in types_to_download:
          date = datetime.datetime.strptime(file_info['recording_start'], '%Y-%m-%dT%H:%M:%SZ')
          tmp_name = f"{meeting_config['name']}-{date}.{file_info['file_extension'].lower()}"


          filename = self.download_webhook_recording(
            file_info["download_url"],
            zoom_body["download_token"],
            tmp_name,
          )
          log.log(logging.INFO, f'File {filename} downloaded for meeting {meeting_id}.')
          result['filename'].append(filename)
          result['date'].append(date)
        else:
          log.log(logging.INFO, f'Skipping file-type: {file_info["file_type"]}')

        if self.zoom_config.delete:
          self.delete_recording(meeting_id, file_info['id'], zoom_token)
      result['success'] = True
      return result

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
