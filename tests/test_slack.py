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

import unittest
from zoom_drive_connector import slack

from zoom_drive_connector.configuration import SlackConfig


class TestSlack(unittest.TestCase):
  def setUp(self):
    self.config_dict = {'channel_name': 'some_channel', 'key': 'random_key'}
    self.conf = SlackConfig(self.config_dict)
    self.api = slack.SlackAPI(self.conf)

  def test_logger(self):
    with self.assertLogs(logger='app', level='INFO') as logger:
      self.api.post_message('Test message!', 'fake-channel')

    self.assertRegex(logger.output[0], '.*Slack notification sent.$')
