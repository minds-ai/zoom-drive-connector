# Zoom-Drive-Connector

This program downloads meeting recordings from Zoom and uploads them to a
specific folder on Google Drive.

This software is particularly helpful for archiving recorded meetings and
webinars on Zoom. It can also be used to distribute VODs (videos on demand) to
public folder in Google Drive. This software aims to fill a missing piece of
functionality in Zoom (post-meeting recording sharing).


## December 2024 update

Support added for Zoom Webhooks. This allows the program to be notified when a new recording is
available. This is a more efficient way to handle new recordings, as the program does not need to
poll the Zoom API every few minutes. The program will now listen for new recordings and upload
them to Google Drive as soon as they are available.

To use this feature, you need to set up a webhook in Zoom. This can be done by following the
instructions in the Zoom API documentation. You will need to provide the URL of the server where
the program is running, and a secret key that will be used to verify the authenticity of the
webhook requests. The secret key should be added to the `config.yaml` file under the `zoom` section.

In addition to the download and upload functionality of recordings, the program can also post
the AI generated summary of the meeting to a Slack channel. Note, that the message will be posted
to the main channel and the summary to the thread of the main message.

To enable this the Slack bot needs the following permissions:
- chat:write
- channels:history
- groups:history



## Setup
Create a file called `config.yaml` with the following contents:
```yaml
zoom:
  account_id: "Zoom account ID"
  client_id: "OAuth client ID"
  client_secret: "OAuth client secret"
  webhook_secret: "Secret when using the webhook, can be ignored if using the polling method"
  delete: true
  meetings:
    - {id: "meeting_id" , name: "Meeting Name", folder_id: "Some Google Drive Folder ID", slack_channel: "channel_ID"}
    - {id: "meeting_id2" , name: "Second Meeting Name", folder_id: "Some Google Drive Folder ID2", slack_channel: "channel_ID2"}
drive:
  credentials_json: "conf/credentials.json"
  client_secret_json: "conf/client_secrets.json"
slack:
  key: "slack_api_key"
internals:
  target_folder: "/tmp"
```
*Note:* It is advised to place this file in the `conf` folder (together with the json credentials)
this folder needs to be referenced when you launch the Docker container (see below).

You will need to fill in the example values in the file above. In order to
fill in some of these values you will need to create developer credentials on
several services. Short guides on each service can be found below.

### Zoom
https://developers.zoom.us/docs/internal-apps/create/#steps-to-create-a-server-to-server-oauth-app

For Zoom the Server-to-Server OAuth app is used. You will need to use the following
[guide](https://developer.zoom.us/docs/windows/introduction-and-pre-requisite/). on the Zoom's
developer site. You need to copy the 'account_id', 'client_id' and 'client_secret' variables into
the `config.yaml` file under the `zoom` section.

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

The `credentials` file will be created during the first start (see below).

### Slack
1. Register a new app using [this link](https://api.slack.com/apps/new).
2. Under "Add features and functionality" select "Permissions".
3. Under 'Scopes' select `chat:write:bot` . When using the Webhook & Summary feature you also
   need to select `channels:history` and `groups:history`.
4. On the same page copy the "OAuth Access Token".
   Paste that value into the configuration file under the `slack` section.
5. Put the ID of the Slack channel to post statuses/summaries in the config file.
   Note, make sure to use the ID and not the name. You can get the ID by looking at the channel details.

## Running the Program in webhook mode

Note for this we assume Azure Functions. In theory any other (serverless) function can be used.

To enable the Zoom webhook functionality, you need to set up a webhook in Zoom. This can be done by
following the instructions in the Zoom API documentation. You will need to provide the URL of the
server where the program is running, and a secret key that will be used to verify the authenticity
of the webhook requests. The secret key should be added to the `config.yaml` file under the `zoom`
section.

Zoom documentation: https://marketplace.zoom.us/docs/api-reference/webhook-reference/

To run the program in Azure Functions, you need to create a new function app and add a new function
to it. You can do this by following the instructions in the Azure Functions documentation.

Azure Functions documentation: https://learn.microsoft.com/en-us/azure/azure-functions/

**In short:**
- Create a new function app in the Azure portal.
- Select the 'Flex Consumption' plan.
  - Set the app name/region/resource group to your preference.
  - Set the runtime stack to 'Python', Version to 3.11 and instance size to 2048 MB.
  - Create a new storage account using the default settings.
  - Everything else can be left as default.
- After deployment add the `Secrets & Configuration` as described below.
- Deploy the app using your favorite method (e.g. VSCode extension, Azure CLI, etc.)



**Secrets & Configuration:**
- If you don't have a 'credentials.json' and 'client_secrets.json' file, you can create them by
  following the instructions in the Google Drive section above.

- The `config.yaml` file should be stored in the Environment Variables of the function app.
  - Environment variable: `ZOOM_DRIVE_SLACK_CONFIG`
- The content of the 'credentials.json' should be stored in the
  Environment Variables of the function app.
  - Environment variable: `GOOGLE_APPLICATION_CREDENTIALS`
- The Zoom Webhook token should be stored in the Environment Variables of the function app.
  - Environment variable: `ZOOM_WEBHOOK_TOKEN`
- The content of the files should be encoded as base64 strings. You can use the following command
  to encode the content of a file as a base64 string:
  ```bash
  base64 -w 0 /path/to/file
  ```



## Running the Program in polling mode
The first time we run the program we have to authenticate it with Google and accept the required
permissions. For this we run the docker container in the interactive mode such that we
can enter the generated token. Instructions on how to pull Docker images from the Github
registry can be found
[here](https://help.github.com/en/articles/configuring-docker-for-use-with-github-package-registry#authenticating-to-github-package-registry).

```bash
$ docker pull docker.pkg.github.com/minds-ai/zoom-drive-connector/zoom-drive-connector:1.2.0
$ docker run -i -v /path/to/conf/directory:/conf \
    docker.pkg.github.com/minds-ai/zoom-drive-connector/zoom-drive-connector:1.2.0
```

Alternatively, you can clone the repository and run `make build VERSION=1.2.0` to build
the container locally. In this case, you will need to exchange the long image name
with the short-form one (`zoom-drive-connector:1.2.0`).

This will print an URL, this URL should be copied in the browser. After accepting the
permissions you will be presented with a token. This token should be pasted in the
terminal. After the token has been accepted a `credentials.json` file will have been
created in your configuration folder. You can now kill (`ctrl-C`) the Docker container
and follow the steps below to run it in the background.

Run the following command to start the container after finishing the setup process.
```bash
$ docker run -d -v /path/to/conf/directory:/conf \
    docker.pkg.github.com/minds-ai/zoom-drive-connector/zoom-drive-connector:1.2.0
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
only have to be placed in `environment.yml`. Make sure to record the version of the
package you are adding using the double-equal operator.

To run the program in the conda environment you can use the following command line:
```bash
CONFIG=conf/config.yaml python -u main.py --noauth_local_webserver
```

### Running Tests and Style Checks
All new functionality should have accompanying unit tests. Look at the `tests/`
folder for examples. All tests should be written using the `unittests` framework.
Additionally, ensure that your code conforms with the given style configurations
presented in this repository.

To run tests and style checks, run the following commands:
```bash
$ tox -p all --recreate
$ ./style_checks.sh  # Run this in the root of the repository.
$ # You can also check style for a single file by passing the name of the file.
```

## Contributing
This project is open to public contributions. Fork the project, make any changes you
want, and submit a pull request. Your changes will be reviewed before they are merged
into master.

## Authors
- [Nick Pleatsikas](https://github.com/MrFlynn)
- [Jeroen Bédorf](https://github.com/jbedorf)

## License
This project is licensed under [Apache 2.0](LICENSE).
