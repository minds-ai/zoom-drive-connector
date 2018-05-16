import apiclient
import httplib2
import os

from oauth2client import file, client, tools
from drive import DriveAPIException


class DriveAPI:
  def __init__(self, base_path: str, credentials: str, secrets: str, folder_id: str):
    """Initializes instance of DriveAPI class.

        :param base_path: Path to temporary folder where recordings will be stored.
        :param credentials: Path to credentials.json.
        :param secrets: Path to secrets.json.
        :param folder_id: Target Google Drive folder ID to upload recordings to.
        """

    if base_path.endswith('/'):
      # Remove any trailing forward slashes in path to prevent path errors.
      self._base_path = base_path[:-1]
    else:
      self._base_path = base_path

    self._credentials = credentials
    self._secrets = secrets
    self._folder_id = folder_id

    self._SCOPES = ['https://www.googleapis.com/auth/drive.file']
    self._service = None

    self.setup()

  def setup(self):
    """Triggers the OAuth2 setup flow for Google API endpoints. Requires the ability to open
        a link within a web browser in order to work.
        """
    store = file.Storage(self._credentials)
    creds = store.get()

    if not creds or creds.invalid:
      flow = client.flow_from_clientsecrets(self._secrets, self._SCOPES)
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

    complete_path = '{0}/{1}'.format(self._base_path, filename)
    if not filename or not os.path.exists(complete_path):
      # Raise an exception if the specified file doesn't exist.
      raise DriveAPIException(
          name="File error", reason='{f} could not be found.'.format(f=complete_path))

    # Google Drive file metadata
    metadata = {'name': name, 'parents': [self._folder_id]}

    # Create a new upload of the recording and execute it.
    media = apiclient.http.MediaFileUpload(complete_path, mimetype='video/mp4')
    uploaded_file = self._service\
        .files()\
        .create(body=metadata, media_body=media, fields='webViewLink')\
        .execute()

    # Return the url to the file that was just uploaded.
    return uploaded_file.get('webViewLink')
