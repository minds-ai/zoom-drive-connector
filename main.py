import os
import time
import schedule

import zoom
import slack
import drive
import configuration as config


def download(zoom_conn: zoom.ZoomAPI, zoom_conf: config.ZoomConfig) -> list:
  result = []

  for meeting in zoom_conf.meetings:
    date, storage_url = zoom_conn.pull_file_from_zoom(meeting["id"], rm=zoom_conf.delete)
    if date is not False:
      print("From {} downloaded {}".format(meeting, storage_url))
      name = "{}-{}.mp4".format(date.strftime("%Y%m%d"), meeting["name"])

      result.append({"meeting": meeting["name"], "file": storage_url, "name": name, "date": date})

  return result


def upload(files: list, drive_conn: drive.DriveAPI):
  for file in files:
    try:
      file["url"] = drive_conn.upload_file(file["file"], file["name"])
    except drive.DriveAPIException as e:
      print("Upload failed")
      raise e
    # Remove the file after uploading so we do not run out of disk space in our container
    os.remove(file["file"])


def notify(files: list, slack_conn: slack.SlackAPI):
  for file in files:
    msg = "The recording for the _{}_ meeting on _{}_ is <{}| now available>".format(
        file["meeting"], file["date"].strftime("%B %d, %Y"), file["url"])
    slack_conn.post_message(msg)


def all_steps(zoom_conn: zoom.ZoomAPI,
              slack_conn: slack.SlackAPI,
              drive_conn: drive.DriveAPI,
              zoom_config: config.ZoomConfig):
  downloaded_files = download(zoom_conn, zoom_config)

  for file in downloaded_files:
    print(f'Got {file["file"]}')
    print(file)

  upload(downloaded_files, drive_conn)
  notify(downloaded_files, slack_conn)


if __name__ == '__main__':
  # App configuration.
  app_config = config.ConfigInterface('config.yaml')

  # Configure each API service module.
  zoom_api = zoom.ZoomAPI(app_config.zoom, app_config.internal)
  slack_api = slack.SlackAPI(app_config.slack)
  drive_api = drive.DriveAPI(app_config.drive, app_config.internal)  # This should open a prompt.

  # Run the application on a schedule.
  schedule.every(10).minutes.do(all_steps, zoom_api, slack_api, drive_api, app_config.zoom)
  while True:
    schedule.run_pending()
    time.sleep(1)
