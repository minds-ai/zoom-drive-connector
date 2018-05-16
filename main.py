"""

The webhook will initiate the download. 
The webhook has to listen on port 80 or 443 according to 
the zoom documentation.



"""

import datetime
import os
import time


import schedule

from zoom.zoom_api_exception import ZoomAPIException
from zoom.zoom_api import ZoomAPI
from slack.slack_api import SlackAPI
from drive.drive_api import DriveAPI
from drive.drive_api_exception import DriveAPIException
from configuration.configuration_interfaces import *

from flask import Flask, request, abort

import threading

app = Flask(__name__)


def handle_response(data):
  print("Going to work on: ", data)
  
  return


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print(request.json)
        
        # Verification of the incoming json/ID
        
        # Take async follow up actions
        t = threading.Thread(target=handle_response, args=(request.json,))
        t.start()

        
        return '', 200
    else:
        abort(400)

def all_steps(config):
    download_files = download(config.zoom_conf)
    
    for file in download_files:
        print("Got: ", file["file"])
        print(file)
        
      
    upload(download_files, config.drive_conf)
    notify(download_files, config.slack_conf)
        
def download(zoom_conf) -> list:
    zoom = ZoomAPI(zoom_conf)
    
    result = []
    
    for meeting in zoom_conf.meetings:
        date, storage_url = zoom.pull_file_from_zoom(meeting["id"], rm = zoom_conf.delete)
        if date != False:
            print("From {} downloaded {}".format(meeting, storage_url))
            name = "{}-{}.mp4".format(date.strftime("%Y%m%d"),  meeting["name"])

            result.append({
                "meeting" : meeting["name"], 
                "file" : storage_url,
                "name" : name,
                "date" : date})
        
    return result
    
def upload(files : list, drive_conf):    
    drive = DriveAPI("", drive_conf.key, drive_conf.secret, drive_conf.folder_id)
    
    for file in files:
        try:
            file["url"] = drive.upload_file(file["file"], file["name"])
        except DriveAPIException as e:
            print("Upload failed")
            raise e
        #Remove the file after uploading so we do not run out of disk space in our container
        os.remove(file["file"])
    

def notify(files : list, slack_conf):
    slack = SlackAPI(slack_conf)
    for file in files:
        msg = "The recording for the _{}_ meeting on _{}_ is <{}| now available>".format(file["meeting"],
                 file["date"].strftime("%B %d, %Y"), file["url"])
        slack.post_message(msg)
        

#Run as Python main.py --noauth_local_webserver
if __name__ == '__main__':
    config = ConfigInterface("config.yaml")
    
    # Run authenthication at start so we do get a prompt when running in a docker container
    drive = DriveAPI("", config.drive_conf.key, config.drive_conf.secret, config.drive_conf.folder_id)# DriveAPI("", "credentials.json", "client_secrets.json", "1PLX1SoyFgvpCVfCSNo5h84czWH8S3m0W")
        
    all_steps(config)

       
    #app.run(port=12399, debug=True,host='0.0.0.0')
    #threaded = True
    schedule.every(10).minutes.do(all_steps, config)
    while 1:
        schedule.run_pending()
        time.sleep(1)
