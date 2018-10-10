import logging
import os
import time
import schedule

import zoom
import slack
import drive
import configuration as config


def download(zoom_conn: zoom.ZoomAPI, zoom_conf: config.ZoomConfig) -> list:
  """Downloads all available recordings from Zoom and returns a list of dicts with all relevant
  information about the recording.

  :param zoom_conn: API object instance for Zoom.
  :param zoom_conf: configuration instance containing all Zoom API settings.
  :return: list of dictionaries containing meeting recording information.
  """
  result = []

  for meeting in zoom_conf.meetings:
    res = zoom_conn.pull_file_from_zoom(meeting['id'], rm=zoom_conf.delete)
    if (res['success']) and ('filename' in res):
      name = '{}-{}.mp4'.format(res['date'].strftime('%Y%m%d'), meeting['name'])

      result.append({'meeting': meeting['name'],
                     'file': res['filename'],
                     'name': name,
                     'date': res['date'].strftime('%B %d, %Y')})

  return result


def upload_and_notify(files: list, drive_conn: drive.DriveAPI, slack_conn: slack.SlackAPI):
  """Uploads a list of files from the local filesystem to Google Drive.

  :param files: list of dictionaries containing file information.
  :param drive_conn: API instance for Google Drive.
  :param slack_conn: API instance for Slack.
  """
  for file in files:
    try:
      # Get url from upload function.
      file_url = drive_conn.upload_file(file['file'], file['name'])

      # Only post message if the upload worked.
      message = 'The recording _{}_ meeting on _{}_ is <{}| now available>.'.format(
        file['meeting'],
        file['date'],
        file_url)
      slack_conn.post_message(message)
    except drive.DriveAPIException as e:
      raise e
    # Remove the file after uploading so we do not run out of disk space in our container.
    os.remove(file['file'])


def all_steps(zoom_conn: zoom.ZoomAPI,
              slack_conn: slack.SlackAPI,
              drive_conn: drive.DriveAPI,
              zoom_config: config.ZoomConfig):
  """Primary function dispatcher that calls functions which download files and then upload them and
  notifies people in Slack that they are on Google Drive.

  :param zoom_conn: API object instance for Zoom.
  :param slack_conn: API object instance for Slack.
  :param drive_conn: API object instance for Google Drive.
  :param zoom_config: configuration instance containing all Zoom API settings.
  """
  downloaded_files = download(zoom_conn, zoom_config)
  upload_and_notify(downloaded_files, drive_conn, slack_conn)


if __name__ == '__main__':
  # App configuration.
  app_config = config.ConfigInterface(os.getenv('CONFIG', '/conf/config.yaml'))

  # Configure each API service module.
  zoom_api = zoom.ZoomAPI(app_config.zoom, app_config.internals)
  slack_api = slack.SlackAPI(app_config.slack)
  drive_api = drive.DriveAPI(app_config.drive, app_config.internals)  # This should open a prompt.

  # Run the application on a 10 minute schedule.
  all_steps(zoom_api, slack_api, drive_api, app_config.zoom)
  schedule.every(10).minutes.do(all_steps, zoom_api, slack_api, drive_api, app_config.zoom)
  while True:
    schedule.run_pending()
    time.sleep(1)
