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

import logging
from typing import TypeVar, cast

from slackclient import SlackClient
from zoom_drive_connector.configuration import SlackConfig, APIConfigBase

log = logging.getLogger('app')
S = TypeVar("S", bound=APIConfigBase)


class SlackAPI:
  def __init__(self, config: S):
    """Class initialization. Stores link config and initializes client with supplied key.

    :param config: Slack configuration object.
    """
    self.config = cast(SlackConfig, config)
    self.sc = SlackClient(self.config.key)

  def post_message(self, text: str, channel: str):
    """Sends message to specific Slack channel with given payload.

    :param text: message to sent to Slack channel.
    :param channel: channel name or ID to send `text` to.
    :return: None.
    """
    self.sc.api_call('chat.postMessage', channel=channel, text=text)
    log.log(logging.INFO, 'Slack notification sent.')
