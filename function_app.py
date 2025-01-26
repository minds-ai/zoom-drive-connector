# Copyright 2024 Minds.ai, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Azure Function App to handle ad process Zoom Webhooks events.

Supported Events:
- recording.completed: Triggered when the recording of a meeting is completed and available.
    The event body contains a download link.
- meeting.summary_completed: Triggered when the summary of a meeting is completed and available.
    The event body contains the summary data.
"""

import json
import logging
import os

import azure.functions as func
from azure.functions.decorators import FunctionApp

from zoom_drive_connector import configuration as config
from zoom_drive_connector import drive, slack, zoom

app = FunctionApp()


def get_apis(use_zoom: bool = True, use_slack: bool = True, use_drive: bool = True) -> tuple:
    """Initialize all APIs and return the objects.

    Args:
        use_zoom: Whether to use the Zoom API.
        use_slack: Whether to use the Slack API.
        use_drive: Whether to use the Google Drive API.

    Returns:
        Tuple of ZoomAPI, SlackAPI, and DriveAPI objects
    """
    app_config = config.ConfigInterface("")
    zoom_api = zoom.ZoomAPI(app_config.zoom, app_config.internals) if use_zoom else None
    slack_api = slack.SlackAPI(app_config.slack) if use_slack else None
    drive_api = drive.DriveAPI(app_config.drive, app_config.internals) if use_drive else None
    return zoom_api, slack_api, drive_api


@app.route(route="zoom", methods=["POST"])
@app.queue_output(arg_name="queue", queue_name="myqueue", connection="AzureWebJobsStorage")
def zoom_handle(req: func.HttpRequest, queue: func.Out[str]) -> func.HttpResponse:
    """Handle Zoom Webhook events as received from the Zoom systems."""
    logging.info("HTTP trigger function processed a request.")

    headers = req.headers
    text = req.get_body().decode("utf-8")
    zhook = zoom.ZoomWebhook(os.environ["ZOOM_WEBHOOK_TOKEN"])

    try:
        if not zhook.verify_headers(headers, text):
            return func.HttpResponse("Invalid Headers", status_code=400)

        logging.info("Zoom Headers Verified")

        body = req.get_json()
        print(body)

        response = {}
        event_name = body.get("event", "UNKNOWN")

        supported_events = [
            "recording.completed",
            "meeting.summary_completed",
        ]

        logging.info(f"Parsing Event: {event_name}")
        if event_name == "endpoint.url_validation":
            response = zhook.handle_validation_event(body)
        elif event_name in supported_events:
            logging.info(f"Supported Event '{event_name}', added to Queue")
            response = {"message": "Received Supported Event"}
            queue.set(body)
        else:
            response = {"message": "Unsupported Event"}
            logging.warning(f"Unsupported Event: {event_name}")

        return func.HttpResponse(
            json.dumps(response).encode("utf-8"),
            status_code=200,
            headers={"Content-Type": "application/json"},
        )
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse("An error occurred while processing the request.", status_code=500)


@app.queue_trigger(arg_name="msg", queue_name="myqueue", connection="AzureWebJobsStorage")
def process_queue(msg: func.QueueMessage) -> None:
    """Process the message that was added to the queue by the webhook handler."""
    logging.info(f"Queue trigger function processed a message: {msg.get_body().decode('utf-8')}")

    zoom_body = json.loads(msg.get_body().decode("utf-8"))
    event_name = zoom_body["event"]

    if event_name == "recording.completed":
        return process_recording_complete_event(zoom_body)
    if event_name == "meeting.summary_completed":
        return process_meeting_summary_event(zoom_body)

    logging.warning(f"Unsupported Event: {event_name}")


def process_meeting_summary_event(zoom_body: dict) -> None:
    """Process the meeting summary event.

    Args:
        zoom_body: The body of the Zoom event.
    """
    logging.info("Processing meeting summary event")
    try:
        zoom_api, slack_api, _ = get_apis(use_drive=False)
        result = zoom_api.webhook_summary_message(zoom_body)

        if result["success"]:
            slack_api.post_summary(result, result["slack_channel"])
            logging.info("Meeting summary event processed successfully")
    except Exception as e:
        logging.error(f"Error processing meeting summary event: {e}", exc_info=True)


def process_recording_complete_event(zoom_body: dict) -> None:
    """Process the recording completed event.

    Args:
        zoom_body: The body of the Zoom event.
    """
    logging.info("Processing meeting recording event")
    try:
        zoom_api, slack_api, drive_api = get_apis()
        result = zoom_api.webhook_recording_complete(zoom_body, ["MP4"])

        if (result["success"]) and (result["filename"]):
            logging.info(f"Successfully downloaded {result['filename']}")
        else:
            logging.error(f"Failed to download files: {result}")
            return

        for idx, fname in enumerate(result["filename"]):
            try:
                name = f'{result["date"][idx].strftime("%Y%m%d")}-{result["meeting"]}.mp4'
                slack_api.post_recording_message(
                    result["meeting"],
                    result["date"][idx],
                    drive_api.upload_file(fname, name, result["folder_id"]),
                    result["meeting_uuid"],
                    result["slack_channel"],
                )
            except drive.DriveAPIException as e:
                raise e
            # Remove the file after uploading so we do not run out of disk space in our container.
            os.remove(fname)
    except Exception as e:
        logging.error(f"Error processing queue message: {e}", exc_info=True)
