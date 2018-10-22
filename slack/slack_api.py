import logging
from typing import Union

from slackclient import SlackClient

from configuration.configuration_interfaces import SlackConfig

log = logging.getLogger('app')


class SlackAPI:
  def __init__(self, config: SlackConfig):
    """Class initialization. Stores link config and initializes client with supplied key.

    :param config: Slack configuration object.
    """
    self.config = config
    self.sc = SlackClient(self.config.key)

  def post_message(self, text: str, channel: Union[str, int] = None):
    """Sends message to specific Slack channel with given payload.

    :param text: message to sent to Slack channel.
    :param channel: channel name or ID to send `text` to.
    :return: None.
    """
    if not channel:
      channel = self.config.channel
    self.sc.api_call('chat.postMessage', channel=channel, text=text)
    log.log(logging.INFO, 'Slack notification sent.')
