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
            # Pick download url for video recording, not audio recording.
            for r in zoom_request.json()[0]['recording_files']:
                if r['file_type'] == 'MP4':
                    return r['download_url']
    @staticmethod
    def get_recording_url_v2(meeting_id: str, auth: str) -> str:
        """Given a specific meeting room ID and auth token, this function gets the download url
        for most recent recording in the given meeting room.

        :param meeting_id: UUID associated with a meeting room.
        :param auth: Encoded JWT authorization token
        """
        zoom_url = 'https://api.zoom.us/v2/meetings/{id}/recordings'.format(id=meeting_id)
        zoom_request = requests.get(zoom_url, params={"access_token" : auth})

        if zoom_request.status_code == 401:
            # Handle unauthenticated requests.
            raise ZoomAPIException(401, 'Unauthorized', zoom_request.request, 'Not authenticated.')
        else:
            # Pick download url for video recording, not audio recording.
            for r in zoom_request.json()['recording_files']:
                if r['file_type'] == 'MP4':
                    return r['download_url']

    @staticmethod
    def get_recording_url_user(user_id: str, auth_token: str) -> str:
        """Given a specific user ID and auth token, this function gets the download url
        for most recent recording in the given meeting room.
        TODO(jbedorf): Right now it just returns a URL, not guaranteed to be the last one

        :param user_id: User ID associated with a user
        :param auth: encoded JWT token.
        """

        payload = {
            'from' : '2018-05-01T00:00:00.000Z',
            'to'   : '2018-05-10T00:00:00.000Z',
            'access_token' : auth_token
        }

        zoom_url = 'https://api.zoom.us/v2/users/{id}/recordings'.format(id=user_id)
        zoom_request = requests.get(zoom_url, params=payload)

        if zoom_request.status_code == 401:
            # Handle unauthenticated requests.
            raise ZoomAPIException(401, 'Unauthorized', zoom_request.request, 'Not authenticated.')
        else:
            # Pick download url for video recording, not audio recording.
            for r in zoom_request.json()["meetings"]:
                for f in r['recording_files']:
                    if f['file_type'] == 'MP4':
                        print(f['download_url'])
                        return f['download_url']

    def download_recording_v2(self, url: str, username: str, password: str):
        """
        """

        import logging

        # These two lines enable debugging at httplib level (requests->urllib3->http.client)
        # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
        # The only thing missing will be the response.body which is not logged.
        try:
            import http.client as http_client
        except ImportError:
            # Python 2
            import httplib as http_client
        http_client.HTTPConnection.debuglevel = 1

        # You must initialize logging, otherwise you'll not see debug output.
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

        zoomSignInURL="https://api.zoom.us/signin"

        #TODO(jbedorf): Do actual login, requires username/password

        session = requests.Session()

        #Until login works use session cookies taken from the browser
        cookies={
        '_zm_mtk_guid' : '<enter>',
        '_zm_ssid' : '<enter>',
        }


        response = session.get(url, cookies=cookies)
        if response.status_code == 200:
            with open("/tmp/test.mp4".encode('utf-8'), 'wb') as f:
                f.write(response.content)
            return True
        return False



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
