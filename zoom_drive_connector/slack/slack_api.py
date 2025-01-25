# Copyright 2018 Minds.ai, Inc. All Rights Reserved.
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

import datetime
import enum
import logging
from typing import Any, Dict, TypeVar, cast

from slack import WebClient
from zoom_drive_connector.configuration import SlackConfig, APIConfigBase

log = logging.getLogger('app')
S = TypeVar("S", bound=APIConfigBase)

class SlackMessages(enum.Enum):
  RECORDING_AVAILABLE = "The recording is available "
  RECORDING_UNAVAILABLE = "The recording is not available."
  SUMMARY_AVAILABLE = "The summary is available in the thread."
  SUMMARY_UNAVAILABLE = "The summary is not (yet) available."


class SlackAPI:
  def __init__(self, config: S):
    """Class initialization. Stores link config and initializes client with supplied key.

    :param config: Slack configuration object.
    """
    self.config = cast(SlackConfig, config)
    self.sc = WebClient(self.config.key)


  def post_message(self, text: str, channel: str):
    """Sends message to specific Slack channel with given payload.

    :param text: message to sent to Slack channel.
    :param channel: channel name or ID to send `text` to.
    :return: None.
    """
    self.sc.chat_postMessage(channel=channel, text=text)
    log.log(logging.INFO, 'Slack notification sent.')


  def _create_meeting_message(self, meeting_name, date, file_url, meeting_uuid, summary_set: bool = False):
    """Creates a message for a meeting recording.

    :param meeting_name: name of the meeting.
    :param date: date of the meeting.
    :param file_url: link to the recording.
    :return: formatted message.
    """
    if file_url:
      recording_block = [
        { "type": "text", "text": SlackMessages.RECORDING_AVAILABLE.value },
        { "type": "link", "text": "here.", "url": file_url },
    ]
    else:
      recording_block = [{"type": "text", "text": SlackMessages.RECORDING_UNAVAILABLE.value}]

    date_str = self._get_date_str(date)
    summary = SlackMessages.SUMMARY_AVAILABLE.value if summary_set else SlackMessages.SUMMARY_UNAVAILABLE.value
    text = f"The \"{meeting_name}\" meeting, held on {date_str}, has concluded."
    return [
      {"type": "section", "block_id": meeting_uuid, "text": { "type": "mrkdwn", "text": text}},
      {
        "type": "rich_text",
        "elements": [
          {
            "type": "rich_text_list",
            "style": "bullet",
            "elements": [
              { "type": "rich_text_section", "elements": recording_block},
              { "type": "rich_text_section", "elements": [{"type": "text", "text": summary}] }
            ]
          }
        ]
      }
    ]


  def _find_previous_top_post(self, channel: str, meeting_uuid: str) -> Dict[str, Any]:
    """Finds if there is a previous post in the Slack channel related to this meeting.

    :param channel: channel name or ID to search in.
    :param meeting_uuid: unique identifier for the meeting.
    :return: dictionary containing post information.
    """
    # Only search for messages in the last 4 hours, anything older should not be relevant.
    oldest = (datetime.datetime.now() - datetime.timedelta(hours=4)).timestamp()

    for message in self.sc.conversations_history(channel=channel, oldest=oldest).data["messages"]:
      if "blocks" not in message or message["blocks"][0].get("block_id") != meeting_uuid:
        continue

      # Found an existing block, check if we have a URL and summary
      items = message.get("blocks")[1]["elements"][0]["elements"][0]["elements"]
      url = items[1]["url"] if len(items) > 1 else None

      items = message.get("blocks")[1]["elements"][0]["elements"][1]["elements"]
      has_summary = items[0]["text"] == SlackMessages.SUMMARY_AVAILABLE.value

      return message, url, has_summary
    return None, "", False


  def post_top_message(
      self,
      channel: str,
      name: str,
      meeting_date: datetime.datetime,
      meeting_uuid: str,
      url: str,
      has_summary: bool,
    ):
    """Posts a message related to this meeting.

    :param channel: channel name or ID to send a message to.
    :param name: name of the meeting.
    :param meeting_date: date of the meeting.
    :param meeting_uuid: unique identifier for the meeting.
    :param url: URL to the recording.
    :param has_summary: if a summary is available.
    :return: None.
    """
    # Check if there is an existing post for this meeting and see if it has a recording/summary.
    existing_post, url2, has_summary2 = self._find_previous_top_post(channel, meeting_uuid)
    url = url if url else url2
    has_summary = has_summary or has_summary2

    top_msg = self._create_meeting_message(name, meeting_date, url, meeting_uuid, has_summary)

    thread_ts = None
    if existing_post:
      self.sc.chat_update(channel=channel, ts=existing_post["ts"], blocks=top_msg)
      thread_ts = existing_post["ts"]
    else:
      result = self.sc.chat_postMessage(channel=channel, blocks=top_msg)
      thread_ts=result.data["ts"]

    log.log(logging.INFO, f'Slack top-message sent to {channel}.')
    return thread_ts


  def post_recording_message(self, name: str, date: str, url: str, meeting_uuid: str, channel: str):
    """Sends message to specific Slack channel with given payload.

    :param text: message to sent to Slack channel.
    :param channel: channel name or ID to send `text` to.
    :return: None.
    """
    self.post_top_message(channel, name, date,meeting_uuid, url, False)
    log.log(logging.INFO, 'Slack notification sent for available recording.')


  def post_summary(self, summary_data: Dict[str, Any], channel: str):
    """Posts a summary message to a Slack channel.

    :param summary_data: dictionary containing summary information.
    :param channel: channel name or ID to send the message to.
    """
    summary = summary_data["summary"]
    name = summary_data["meeting"]
    blocks = []
    blocks.extend(self._get_summary_header(summary, name))
    blocks.append(self._get_richtext_section("Overview", summary['overview']))
    blocks.extend(self._get_summary_next_steps(summary))
    blocks.append({"type": "divider"})
    blocks.append(self._get_richtext_section("Summary", ""))
    blocks.extend(self._get_summary_details(summary))

    thread_ts = self.post_top_message(
      channel, name, summary['date'], summary_data["meeting_uuid"], "", True
    )
    self.sc.chat_postMessage(channel=channel, blocks=blocks, thread_ts=thread_ts)
    log.log(logging.INFO, f'Slack summary sent to {channel}.')


  def _get_date_str(self, date: datetime.datetime) -> str:
    """Returns a formatted date string.

    :param date: datetime object to format.
    :return: formatted date string.
    """
    date_time_str = date.strftime('%B %d, %Y at %H:%M')
    unix = int(date.replace(tzinfo=datetime.timezone.utc).timestamp())
    return "<!date^" + str(unix) + "^{date} at {time}|" + date_time_str +" UTC + >"

  def _get_summary_header(self, summary: Dict[str, Any], name: str) -> Dict[str, Any]:
    """Returns a header block for a Slack message.

    The date is formatted as a Unix timestamp for Slack to convert to the user's local time.

    :param summary: dictionary containing summary information.
    :return: dictionary containing header block.
    """
    return [
        {
        "type": "header",
        "text": {
          "type": "plain_text",
          "text": f"Summary for '{name}' - {summary['date'].strftime('%B %d, %Y')}",
        }
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text":f"(*{self._get_date_str(summary['date'])}*)"
        }
      }
    ]


  def _get_summary_details(self, summary: Dict[str, Any]) -> Dict[str, Any]:
    """Returns a block for the summary overview.

    :param summary: dictionary containing summary information.
    :return: List of summary sections.
    """
    return [
      self._get_richtext_section(section["label"], section["summary"])
      for section in summary["details"]
    ]


  def _get_richtext_section(self, title, content) -> Dict[str, Any]:
      return {
        "type": "section",
        "text": { "type": "mrkdwn", "text": f"*{title}*\n{content}" }
      }

  def _get_summary_next_steps(self, summary: Dict[str, Any]) -> Dict[str, Any]:
    """Returns a block for the next steps to be taken.

    :param summary: dictionary containing summary information.
    :return: dictionary containing next steps block.
    """

    next_steps=summary["next_steps"]
    if not next_steps:
      return []

    list_items = [
      {"type": "rich_text_section", "elements": [{"type": "text", "text": item}]}
      for item in next_steps
    ]
    elements = [
      {
          "type": "rich_text_section", "elements": [
              { "type": "text", "text": "Next Steps", "style": { "bold": True }}
        ]
      },
      {"type": "rich_text_list", "style": "bullet", "elements": list_items}
    ]

    return [
      {"type": "section", "text": { "type": "mrkdwn", "text": "\n" }},
			{"type": "rich_text", "elements": elements }
    ]

