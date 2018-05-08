import datetime
import jwt
import os
import time
import shutil

import dateutil.parser
import requests
from zoom import ZoomAPIException
from configuration.configuration_interfaces import ZoomConfig


class ZoomAPI:
    def __init__(self, config : ZoomConfig, fs_target: str = '/tmp'):
        """Class initialization; sets client key, secret, and download folder path.

        :param key: Zoom client key.
        :param secret: Zoom client secret.
        :param fs_target: Path to download folder. Default is /tmp.
        """
        self.config = config 
        self.fs_target = fs_target
        
        # Information required to login to allow downloads
        self.zoomSignInURL="https://api.zoom.us/signin"
        self.timeout = 1800  # Default expiration time is 30 minutes.

    def generate_jwt(self) -> str:
        """Generates the JSON web token used for authenticating with Zoom. Sends client key
        and expiration time encoded with the secret key.
        """
        payload = {'iss': self.config.key, 'exp': int(time.time()) + self.timeout}
        return jwt.encode(payload, self.config.secret, algorithm='HS256')

    @staticmethod
    def delete_recording(meeting_id: str, auth: dict, recording_id: type = None):
        """Given a specific meeting room ID, this function trashes all recordings associated with
        that room ID.

        :param meeting_id: UUID associated with a meeting room.
        :param auth: JWT token.
        :param recording_id: The ID of the recording to delete, if None delete all recordings.
        """
        
        # TODO(jbedorf): This function is untested, 
        
        if recording_id:
            zoom_url = 'https://api.zoom.us/v2/meetings/{id}/recordings/{rid}'.format(
                id=meeting_id, rid=recording_id)
        else:
            zoom_url = 'https://api.zoom.us/v2/meetings/{id}/recordings'.format(id=meeting_id)
        res = requests.delete(zoom_url, params={"access_token" : auth, action : "trash"})

        if res.status_code == 401:
            # Handle unauthenticated requests.
            raise ZoomAPIException(401, 'Unauthorized', res.request, 'Not authenticated.')
        elif res.status_code == 409:
            # Handle error where content may have been removed already.
            raise ZoomAPIException(409, 'Resource Conflict', res.request, 'File deleted already.')

    @staticmethod
    def get_recording_url(meeting_id: str, auth: str) -> (datetime.datetime, str):
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
            #print(zoom_request.json()) note this print does not work inside the docker container
            # Pick download url for video recording, not audio recording.
            for r in zoom_request.json()['recording_files']:
                if r['file_type'] == 'MP4':
                    date = dateutil.parser.parse(r['recording_start'])
                    return (date, r['download_url'])

    def download_recording(self, url: str) -> str:
        """Downloads video file from Zoom to local folder.

        :param url: Download URL for meeting recording.
        
        Return:
            Path to the recording
        """
               
        session = requests.Session()
        session.headers.update({'content-type': 'application/x-www-form-urlencoded'})
              
        response = session.post(self.zoomSignInURL, data={'email': self.config.username, 'password': self.config.password}) 
       
        
        filename = url.split('/')[-1]
        zoom_request = session.get(url, stream=True)

        outfile = os.path.join(self.fs_target, filename + ".mp4")
        with open(outfile, 'wb') as source:
            shutil.copyfileobj(zoom_request.raw, source) # Copy raw file data to local file.
        return outfile

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
            date, zoom_url = self.get_recording_url(meeting_id, zoom_token)
            
            print("Recording URL: ", zoom_url)
           
            filename = self.download_recording(zoom_url)
            
            print("Download complete")
            return (date, filename)
            #TODO(jbedorf): Enable the deletion

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
        
      
    @staticmethod
    def get_recording_url_user(user_id: str, auth_token: str) -> str:
        """
        Given a specific user ID and auth token, this function gets the download url
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
