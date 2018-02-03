import jwt
import time
import shutil
import requests
from zoom import ZoomAPIException


class ZoomAPI:
    def __init__(self, key: str, secret: str, fs_target: str = '/tmp'):
        """Class initialization; sets client key, secret, and download folder path.

        :param key: Zoom client key.
        :param secret: Zoom client secret.
        :param fs_target: Path to download folder. Default is /tmp.
        """
        self.key = key
        self.secret = secret
        self.fs_target = fs_target

        self.timeout = 1800  # Default expiration time is 30 minutes.

    def generate_jwt(self) -> str:
        """Generates the JSON web token used for authenticating with Zoom. Sends client key
        and expiration time encoded with the secret key.
        """
        payload = {'iss': self.key, 'exp': int(time.time()) + self.timeout}
        return jwt.encode(payload, self.secret, algorithm='HS256')

    @staticmethod
    def delete_recording(meeting_id: str, auth: dict):
        """Given a specific meeting room ID, this function trashes all recordings associated with
        that room ID.

        :param meeting_id: UUID associated with a meeting room.
        :param auth: Authorization Bearer with encoded JWT.
        """
        zoom_url = 'https://api.zoom.us/v2/meetings/{id}/recordings'.format(id=meeting_id)
        res = requests.delete(zoom_url, headers=auth)

        if res.status_code == 401:
            # Handle unauthenticated requests.
            raise ZoomAPIException(401, 'Unauthorized', res.request, 'Not authenticated.')
        elif res.status_code == 409:
            # Handle error where content may have been removed already.
            raise ZoomAPIException(409, 'Resource Conflict', res.request, 'File deleted already.')

    @staticmethod
    def get_recording_url(meeting_id: str, auth: dict) -> str:
        """Given a specific meeting room ID and auth token, this function gets the download url
        for most recent recording in the given meeting room.

        :param meeting_id: UUID associated with a meeting room.
        :param auth: Authorization Bearer with encoded JWT.
        """
        zoom_url = 'https://api.zoom.us/v2/meetings/{id}/recordings'.format(id=meeting_id)
        zoom_request = requests.get(zoom_url, headers=auth)

        if zoom_request.status_code == 401:
            # Handle unauthenticated requests.
            raise ZoomAPIException(401, 'Unauthorized', zoom_request.request, 'Not authenticated.')
        else:
            return zoom_request.json()[0]['recording_files']['download_url']

    def download_recording(self, url: str, auth: dict):
        """Downloads video file from Zoom to local folder.

        :param url: Download URL for meeting recording.
        :param auth: Authorization bearer header with encoded JWT.
        """
        filename = url.split('/')[-1]
        zoom_request = requests.get(url, headers=auth, stream=True)

        with open(self.fs_target + filename, 'wb') as source:
            shutil.copyfileobj(zoom_request.raw, source) # Copy raw file data to local file.

    def pull_file_from_zoom(self, meeting_id: str, rm: bool = True) -> bool:
        """Interface for downloading recordings from Zoom. Optionally trashes recorded file on Zoom.
        Returns true if all processes completed successfully.

        :param meeting_id: UUID for meeting room where recording was just completed.
        :param rm: If true is passed (default) then file is trashed on Zoom.
        """
        try:
            # Generate token and Authorization header.
            zoom_token = self.generate_jwt()
            zoom_auth = {'Authorization': 'Bearer {jwt}'.format(jwt=zoom_token)}
            
            # Get URL and download the file.
            zoom_url = self.get_recording_url(meeting_id, zoom_auth)
            self.download_recording(zoom_url, zoom_auth)

            if rm:
                self.delete_recording(meeting_id, zoom_auth)

            return True
        except ZoomAPIException as ze:
            print(ze)

            if ze.http_method == 'DELETE':
                # Allow other systems to proceed if delete fails.
                return True
            else:
                return False
        except OSError as fe:
            # Catches general filesystem errors. If download coult not be written to disk, stop.
            print(fe)
            return False
