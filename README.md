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
    - {id: "meeting_id2" , name: "Second Meeting Name"}
drive:
  credentials_json: "conf/credentials.json"
  client_secret_json: "conf/client_secrets.json"
  folder_id: "Some Google Drive Folder ID"
slack:
  channel: "channel_name"
  key: "slack_api_key"
internals:
  target_folder: /tmp
``` 
*Note:* It is advised to place this file in the `conf` folder (together with the json credentials)
this folder needs to be referenced when you launch the Docker container (see below).

You will need to fill in the example values in the file above. In order to 
fill in some of these values you will need to create developer credentials on
several services. Short guides on each service can be found below.

### Zoom
To get the proper API key and secret, you will need to use the following 
"Getting Started Guide" on Zoom's developer site. Link [here](https://developer.zoom.us/docs/windows/introduction-and-pre-requisite/).
Paste the API key and secret into `config.yaml` under the `zoom` section.

It is (currently) not possible to download the recordings via the API key. 
As such you need to create a new Zoom user within your organizations Zoom account. 
This can be a non-pro user. It is important that this user logs in via a username 
and password. The username and password for this account should be added 
to the `username` and `password` entrees under the `zoom` section.

### Google Drive
To upload files to Google Drive you have to login to your developer console, create a new project,
set the required permissions and then download the access key. This can be done via the following
steps:

1. Go to the [Google API Console](https://console.developers.google.com/)
2. Click on "Create new project".
3. Give it a name and enter any other required info.
4. Once back on the dashboard click on "Enable APIs and Services" (make sure your newly 
created project is selected).
5. Search for and enable: "Google Drive API".
6. Go back to the dashboard and click on "Credentials" in the left side bar.
7. On the credentials screen click on the "Create credentials" button and select "OAuth client ID".
8. Follow the instructions to set a product name, on the next screen only the `Application name`
is required. Enter it and click on "save".
9. As application type, select "Other" and fill in the name of your client.
10. Now under "OAuth 2.0 client IDs" download the JSON file for the newly create client ID 
11. Save this file as `client_secrets.json` in the `conf` directory.

The `credentials` file will be created during the first start (see below)

### Slack
1. Register a new app using [this link](https://api.slack.com/apps/new).
2. Under "Add features and functionality" select "Permissions".
3. Under 'Scopes' select `chat:write:bot`.
4. On the same page copy the "OAuth Access Token".
   Paste that value into the configuration file under the `slack` section.
5. Put the name of the Slack channel to post statuses in the config file.

## Running the Program
The first time we run the program we have to authenticate it with Google and accept the required
permissions. For this we run the docker container in the interactive mode such that we 
can enter the generated token. 

```bash
$ cd zoom-drive-connector/
$ make build
$ docker run -i -v /path/to/conf/directory:/conf \
    minds-ai/zoom-drive-connector:latest
```

This will print an URL, this URL should be copied in the browser. After accepting the 
permissions you will be presented with a token. This token should be pasted in the 
terminal. After the token has been accepted a `credentials.json` file will have been 
created in your configuration folder. You can now kill (`ctrl-C`) the Docker container 
and follow the steps below to run it in the background.

Run the following command to start the container after finishing the setup process.
```bash
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
`requirements.txt` with the exception of development dependencies, which 
only have to be placed in `environment.yml`. Make sure to record the version of the package
you are adding using the double-equal operator.

To run the program in the conda environment you can use the following command line:
```bash
CONFIG=conf/config.yaml python -u main.py --noauth_local_webserver
```
