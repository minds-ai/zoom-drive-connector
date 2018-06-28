import datetime
import os
import time
import shutil

import dateutil.parser
import jwt
import requests

from zoom import ZoomAPIException
from configuration.configuration_interfaces import ZoomConfig


class ZoomAPI:
  def __init__(self, config: ZoomConfig, fs_target: str = '/tmp'):
    """Class initialization; sets client key, secret, and download folder path.

    :param key: Zoom client key.
    :param secret: Zoom client secret.
    :param fs_target: Path to download folder. Default is /tmp.
    """
    self.config = config
    self.fs_target = fs_target

    # Information required to login to allow downloads
    self.zoom_signin_url = "https://api.zoom.us/signin"
    self.timeout = 1800  # Default expiration time is 30 minutes.

  def generate_jwt(self) -> str:
    """Generates the JSON web token used for authenticating with Zoom. Sends client key
    and expiration time encoded with the secret key.
    """
    payload = {'iss': self.config.key, 'exp': int(time.time()) + self.timeout}
    return jwt.encode(payload, self.config.secret, algorithm='HS256')

  def delete_recording(self, meeting_id: str, recording_id: str, auth: str):
    """Given a specific meeting room ID, this function trashes all recordings associated with
    that room ID.

    :param meeting_id: UUID associated with a meeting room.
    :param recording_id: The ID of the recording to delete.
    :param auth: JWT token.
    """
    zoom_url = 'https://api.zoom.us/v2/meetings/{id}/recordings/{rid}'.format(
        id=meeting_id, rid=recording_id)
    res = requests.delete(
        zoom_url, params={"access_token": auth,
                          "action": "trash"})  # Note trash, not delete

    if res.status_code == 401:
      # Handle unauthenticated requests.
      raise ZoomAPIException(401, 'Unauthorized', res.request, 'Not authenticated.')
    elif res.status_code == 409:
      # Handle error where content may have been removed already.
      raise ZoomAPIException(409, 'Resource Conflict', res.request, 'File deleted already.')

  def get_recording_url(self, meeting_id: str, auth: str) -> (datetime.datetime, str, str):
    """Given a specific meeting room ID and auth token, this function gets the download url
    for most recent recording in the given meeting room.

    :param meeting_id: UUID associated with a meeting room.
    :param auth: Encoded JWT authorization token
    :return: tuple containing the date of the recording, the ID of the recording, and the video url.
    """
    zoom_url = 'https://api.zoom.us/v2/meetings/{id}/recordings'.format(id=meeting_id)
    zoom_request = requests.get(zoom_url, params={"access_token": auth})

    if zoom_request.status_code == 401:
      # Handle unauthenticated requests.
      raise ZoomAPIException(401, 'Unauthorized', zoom_request.request, 'Not authenticated.')
    elif zoom_request.status_code == 404:  # You get this if there are no files
      raise ZoomAPIException(404, 'File Not Found', zoom_request.request,
                             'File not found or no recordings')
    else:
      print(zoom_request.json())
      for r in zoom_request.json()['recording_files']:
        # TODO(jbedorf) : For now let's just delete the chat messages and
        # continue processing other files
        if r['file_type'] == 'CHAT':
          self.delete_recording(meeting_id, r['id'], auth)
        elif r['file_type'] == 'MP4':
          date = dateutil.parser.parse(r['recording_start'])
          rec_id = r['id']
          return (date, rec_id, r['download_url'])
      raise ZoomAPIException(404, 'File Not Found', zoom_request.request,
                             'File not found or no recordings')

  def download_recording(self, url: str) -> str:
    """Downloads video file from Zoom to local folder.

    :param url: Download URL for meeting recording.
    :return: Path to the recording
    """

    session = requests.Session()
    session.headers.update({'content-type': 'application/x-www-form-urlencoded'})

    response = session.post(
        self.zoom_signin_url, data={'email': self.config.username,
                                  'password': self.config.password})

    response = response  # Make pylint happy
    filename = url.split('/')[-1]
    zoom_request = session.get(url, stream=True)

    outfile = os.path.join(self.fs_target, filename + ".mp4")
    with open(outfile, 'wb') as source:
      shutil.copyfileobj(zoom_request.raw, source)  # Copy raw file data to local file.
    return outfile

  def pull_file_from_zoom(self, meeting_id: str, rm: bool = True) -> (bool, bool):
    """Interface for downloading recordings from Zoom. Optionally trashes recorded file on Zoom.
    Returns true if all processes completed successfully.

    :param meeting_id: UUID for meeting room where recording was just completed.
    :param rm: If true is passed (default) then file is trashed on Zoom.
    :return: tuple of booleans that indicates that bother operations completed sucessfully.
    """
    try:
      # Generate token and Authorization header.
      zoom_token = self.generate_jwt()

      # Get URL and download the file.
      date, rec_id, zoom_url = self.get_recording_url(meeting_id, zoom_token)
      filename = self.download_recording(zoom_url)

      if rm:
        self.delete_recording(meeting_id, rec_id, zoom_token)

      return (date, filename)
    except ZoomAPIException as ze:
      print(ze)

      if ze.http_method == 'DELETE':
        # Allow other systems to proceed if delete fails.
        return (True, True)
      return (False, False)
    except OSError as fe:
      # Catches general filesystem errors. If download coult not be written to disk, stop.
      print(fe)
      return (False, False)
