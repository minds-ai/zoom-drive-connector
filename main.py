"""

The webhook will initiate the download. 
The webhook has to listen on port 80 or 443 according to 
the zoom documentation.



"""

import datetime
import time

import schedule

from zoom.zoom_api_exception import ZoomAPIException
from zoom.zoom_api import ZoomAPI
from slack.slack_api import SlackAPI
from configuration.configuration_interfaces import *



#ZOOMCONFIG = ZoomConfig("key", "secret","user@minds.ai", "user-passwrd", False)
#slack_token ="slack token of the bot"



sconfig = SlackConfig(slack_token, "z-jeroen-bot") # TODO get channel from the yaml config
 
# TODO(jbedorf): How do we retrieve those meeting IDs apart from query?
meetings = {"***REMOVED***" : "CWW2"}
#            "***REMOVED***" : "CWW2"}


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

def all_steps():
    download_files = download()
    
    for file in download_files:
        print("Got: ", file["file"])
        print(file)
      
    upload(download_files)
    notify(download_files)
        
def download() -> list:
    zoom = ZoomAPI(ZOOMCONFIG)
    
    result = []
    
    for meeting in meetings:
        date, storage_url = zoom.pull_file_from_zoom(meeting, rm = False)
        print("From {} downloaded {}".format(meeting, storage_url))
        name = "{}-{}.mp4".format(date.strftime("%Y%m%d"), meetings[meeting])
        
        result.append({
            "meeting" : meetings[meeting], 
            "file" : storage_url,
            "name" : name,
            "date" : date})
        
    return result
    
def upload(files : list):
    
    for file in files:        
        pass

def notify(files : list):
    slack = SlackAPI(sconfig)
    for file in files:
        msg = "The recording for the {} meeting on {} is now available at: {}".format(file["meeting"],
                 file["date"].strftime("%B %d, %Y"), "https://www.google.com")
        slack.post_message(msg)
        

if __name__ == '__main__':
    #app.run(port=12399, debug=True,host='0.0.0.0')
    #threaded = True
    schedule.every(10).minutes.do(all_steps)
    while 1:
        schedule.run_pending()
        time.sleep(1)