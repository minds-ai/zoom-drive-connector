from slackclient import SlackClient

from configuration.configuration_interfaces import SlackConfig


class SlackAPI:
  def __init__(self, config: SlackConfig):
    """Class initialization;

        :param config: Slack configuration object.

        """
    self.config = config
    self.sc = SlackClient(self.config.key)

  def post_message(self, text: str, channel: str = None):
    if not channel:
      channel = self.config.channel
    self.sc.api_call("chat.postMessage", channel=channel, text=text)
