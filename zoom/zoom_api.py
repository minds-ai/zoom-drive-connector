import datetime
import os
import time
import shutil
import logging
import requests
import jwt

from zoom import ZoomAPIException
from configuration import ZoomConfig
from configuration import SystemConfig

log = logging.getLogger('app')


class ZoomAPI:
  def __init__(self, zoom_config: ZoomConfig, sys_config: SystemConfig):
    """Class initialization; sets client key, secret, and download folder path.

    :param zoom_config: configuration class containing all relevant parameters for Zoom API.
    :param sys_config: configuration class containing target folder where to download contains.
    """
    self.zoom_config = zoom_config
    self.sys_config = sys_config

    # Information required to login to allow downloads
    self.zoom_signin_url = 'https://api.zoom.us/signin'
    self.timeout = 1800  # Default expiration time is 30 minutes.

  def generate_jwt(self) -> str:
    """Generates the JSON web token used for authenticating with Zoom. Sends client key
    and expiration time encoded with the secret key.
    """
    payload = {'iss': self.zoom_config.key, 'exp': int(time.time()) + self.timeout}
    return str(jwt.encode(payload, str(self.zoom_config.secret), algorithm='HS256'))

  @staticmethod
  def delete_recording(meeting_id: str, recording_id: str, auth: str):
    """Given a specific meeting room ID and recording ID, this function moves the recording to the
    trash in Zoom's cloud.

    :param meeting_id: UUID associated with a meeting room.
    :param recording_id: The ID of the recording to trash.
    :param auth: JWT token.
    """
    zoom_url = 'https://api.zoom.us/v2/meetings/{id}/recordings/{rid}'.format(
        id=meeting_id, rid=recording_id)
    res = requests.delete(
        zoom_url, params={'access_token': auth,
                          'action': 'trash'})  # trash, not delete
    if res.status_code == 401:
      # Handle unauthenticated requests.
      raise ZoomAPIException(401, 'Unauthorized', res.request, 'Not authenticated.')
    elif res.status_code == 409:
      # Handle error where content may have been removed already.
      raise ZoomAPIException(409, 'Resource Conflict', res.request, 'File deleted already.')

  def get_recording_url(self, meeting_id: str, auth: str) -> dict:
    """Given a specific meeting room ID and auth token, this function gets the download url
    for most recent recording in the given meeting room.

    :param meeting_id: UUID associated with a meeting room.
    :param auth: Encoded JWT authorization token
    :return: dict containing the date of the recording, the ID of the recording, and the video url.
    """
    zoom_url = 'https://api.zoom.us/v2/meetings/{id}/recordings'.format(id=meeting_id)

    try:
      zoom_request = requests.get(zoom_url, params={'access_token': auth})
    except requests.exceptions.RequestException as e:
      # Failed to make a connection so let's just return a 404, as there is no file
      # but print an additional warning in case it was a configuration error
      log.log(logging.ERROR, e)
      raise ZoomAPIException(404, 'File Not Found', None, 'Could not connect')
    if zoom_request.status_code == 401:
      # Handle unauthenticated requests.
      raise ZoomAPIException(401, 'Unauthorized', zoom_request.request, 'Not authenticated.')
    elif zoom_request.status_code == 404:  # You get this if there are no files
      raise ZoomAPIException(404, 'File Not Found', zoom_request.request,
                             'File not found or no recordings')
    else:
      for req in zoom_request.json()['recording_files']:
        # TODO(jbedorf): For now just delete the chat messages and continue processing other files.
        if req['file_type'] == 'CHAT':
          self.delete_recording(meeting_id, req['id'], auth)
        elif req['file_type'] == 'MP4':
          date = datetime.datetime.strptime(req['recording_start'], '%Y-%m-%dT%H:%M:%SZ')
          return {'date': date, 'id': req['id'], 'url': req['download_url']}
      raise ZoomAPIException(404, 'File Not Found', zoom_request.request,
                             'File not found or no recordings')

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

  def pull_file_from_zoom(self, meeting_id: str, rm: bool = True) -> dict:
    """Interface for downloading recordings from Zoom. Optionally trashes recorded file on Zoom.
    Returns a dictionary containing success state and/or recording information.

    :param meeting_id: UUID for meeting room where recording was just completed.
    :param rm: If true is passed (default) then file is trashed on Zoom.
    :return: dict containing if the operation was successful. If downloading and (optionally)
      deleting the recording on Zoom completed successfully, include the recording date and the
      recording filename.
    """
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
        return {'success': True}
      log.log(logging.ERROR, ze)
      return {'success': False}
    except OSError as fe:
      # Catches general filesystem errors. If download could not be written to disk, stop.
      log.log(logging.ERROR, fe)
      return {'success': False}
