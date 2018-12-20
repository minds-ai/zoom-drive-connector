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

import os
import logging
from typing import TypeVar, cast

import httplib2shim
import apiclient
from oauth2client import file, client, tools

from drive import DriveAPIException
from configuration import DriveConfig, SystemConfig, APIConfigBase

log = logging.getLogger('app')
S = TypeVar("S", bound=APIConfigBase)


class DriveAPI:
  def __init__(self, drive_config: S, sys_config: S):
    """Initializes instance of DriveAPI class.

    :param drive_config: configuration class containing all parameters needed for Google Drive.
    :param sys_config: configuration class containing all system related parameters.
    """
    self.drive_config = cast(DriveConfig, drive_config)
    self.sys_config = cast(SystemConfig, sys_config)

    self._scopes = ['https://www.googleapis.com/auth/drive.file']
    self._service = None

    self.setup()

  def setup(self):
    """Triggers the OAuth2 setup flow for Google API endpoints. Requires the ability to open
    a link within a web browser in order to work.
    """
    store = file.Storage(self.drive_config.credentials_json)
    creds = store.get()

    if not creds or creds.invalid:
      flow = client.flow_from_clientsecrets(self.drive_config.client_secret_json, self._scopes)
      creds = tools.run_flow(flow, store)

    self._service = apiclient.discovery.build('drive',
                                              'v3',
                                              http=creds.authorize(httplib2shim.Http()))

    log.log(logging.INFO, 'Drive connection established.')

  def upload_file(self, file_path: str, name: str, folder_id: str) -> str:
    """Uploads the given file to the specified folder id in Google Drive.

    :param file_path: Path to file to upload to Google Drive.
    :param name: Final name of the file
    :return: The url of the file in Google Drive.
    """

    if self._service is None:
      # Raise an exception if setup() hasn't been run.
      raise DriveAPIException(name='Service error', reason='setup() method not called.')

    if not file_path or not os.path.exists(file_path):
      # Raise an exception if the specified file doesn't exist.
      raise DriveAPIException(
          name='File error', reason=f'{file_path} could not be found.')

    # Google Drive file metadata
    metadata = {'name': name, 'parents': [folder_id]}

    # Create a new upload of the recording and execute it.
    media = apiclient.http.MediaFileUpload(file_path, mimetype='video/mp4')

    # pylint: disable=no-member
    uploaded_file = self._service\
        .files()\
        .create(body=metadata, media_body=media, fields='webViewLink', supportsTeamDrives=True)\
        .execute()

    log.log(logging.INFO, f'File {file_path} uploaded to Google Drive')

    # Return the url to the file that was just uploaded.
    return uploaded_file.get('webViewLink')
