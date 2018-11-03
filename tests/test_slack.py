import unittest
import slack

from configuration import SlackConfig


class TestSlack(unittest.TestCase):
  config_dict = slack_config = {'channel_name': 'some_channel', 'key': 'random_key'}
  conf = SlackConfig(config_dict)
  api = slack.SlackAPI(conf)

  def test_logger(self):
    with self.assertLogs(logger='app', level='INFO') as logger:
      self.api.post_message('Test message!', 'fake-channel')

    self.assertRegex(logger.output[0], '.*Slack notification sent.$')
