# Zoom-Drive-Connector

This program downloads meeting recording from Zoom and uploads them to a 
specific folder on Google Drive. It's that simple.

This software is particularly helpful for archiving recorded meetings and 
webinars on Zoom. It can also be used to distribute VODs (videos on demand) to
public folder in Google Drive. This software aims to fill a missing piece of 
functionality in Zoom (after-the-fact video sharing).

## Setup
Clone the repository on to your machine. Create a file called `config.yaml` with 
the following contents:
```yaml
zoom:
  key: "zoom_api_key"
  secret: "zoom_api_secret"
  username: "email@example.com"
  password: "password for email@example.com" # required to download files from Zoom.
  delete: true
  meetings: 
    - {id: "meeting_id" , name: "Meeting Name"}
drive:
  credentials_json: "conf/credentials.json"
  client_secret_json: "conf/client_secrets.json"
  folder_id: "some_folder_id"
slack:
  channel: "channel_name"
  key: "slack_api_key"
internals:
  target_folder: /tmp
``` 
*Note:* you will need to keep track of the directory of this file as it is 
required to run the container. Creating a separate folder for this file is 
recommended.

You will need to fill in the example values in the file above. In order to 
fill in some of these values you will need to create developer credentials on
several services. Short guides on each service can be found below.

### Zoom
To get the proper API key and secret, you will need to use the following 
"Getting Started Guide" on Zoom's developer site. Link [here](https://developer.zoom.us/docs/windows/introduction-and-pre-requisite/).
Paste the API key and secret into `config.yaml` under the `zoom` section.

### Google Drive
TODO(jbedorf): write out how you created the app and downloaded the requisite 
files. Include which permissions were required for the app.

### Slack
1. Register a new app using [this link](https://api.slack.com/apps/new).
2. TODO(jbedorf): list permissions and if this app needs to be registered 
    as a bot. 
3. Copy the "Client Secret" from *App Credentials* section of your app's page.
    Paste that value into the configuration file under the `slack` section.
4. Put the name of the channel to post statuses to in Slack in the config file.

## Running the Program
Run the following commands to start the container:
```bash
$ cd zoom-drive-connector/
$ make build
$ docker run -d -v /path/to/conf/directory:/conf \
    minds-ai/zoom-drive-connector:latest
```

## Making Changes to Source
If you wish to make changes to the program source, you can quickly create a 
Conda environment using the provided `environment.yml` file. Use the following
commands to get started.
```bash
$ conda env create -f environment.yml
$ source activate zoom-drive-connector
``` 

Any changes to dependencies should be recorded in **both** `environment.yml` and
`requirements.txt` with the exception of development dependencies, which can
only be placed in `environment.yml`. Make sure record the version of the package
you are using using the double-equal operator.