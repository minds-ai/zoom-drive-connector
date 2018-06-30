import os

import httplib2
import apiclient

from oauth2client import file, client, tools

from drive import DriveAPIException

from configuration import DriveConfig
from configuration import SystemConfig


class DriveAPI:
  def __init__(self, drive_config: DriveConfig, sys_config: SystemConfig):
    """Initializes instance of DriveAPI class.

    :param drive_config: configuration class containing all parameters needed for Google Drive.
    :param sys_config: configuration class containing all system related parameters.
    """
    self.drive_config = drive_config
    self.sys_config = sys_config

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

    self._service = apiclient.discovery.build('drive', 'v3', http=creds.authorize(httplib2.Http()))

  def upload_file(self, filename: str, name: str) -> str:
    """Uploads the given file to the specified folder id in Google Drive.

    :param filename: Name of the file within the storage folder to upload to Drive.
    :param name: Final name of the file
    :return: The url of the file in Google Drive.
    """

    if self._service is None:
      # Raise an exception if setup() hasn't been run.
      raise DriveAPIException(name="Service error", reason="setup() method not called.")

    complete_path = '{0}/{1}'.format(self.sys_config.target_folder, filename)
    if not filename or not os.path.exists(complete_path):
      # Raise an exception if the specified file doesn't exist.
      raise DriveAPIException(
          name="File error", reason='{f} could not be found.'.format(f=complete_path))

    # Google Drive file metadata
    metadata = {'name': name, 'parents': [self.drive_config.folder_id]}

    # Create a new upload of the recording and execute it.
    media = apiclient.http.MediaFileUpload(complete_path, mimetype='video/mp4')

    # pylint: disable=no-member
    uploaded_file = self._service\
        .files()\
        .create(body=metadata, media_body=media, fields='webViewLink')\
        .execute()

    # Return the url to the file that was just uploaded.
    return uploaded_file.get('webViewLink')
