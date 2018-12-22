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


class TestSettingsBase(unittest.TestCase):
  def setUp(self):
    self.slack_config = {'key': 'random_key'}
    self.zoom_config = {'key': 'some_key',
                        'secret': 'some_secret',
                        'username': 'some@email.com',
                        'delete': True,
                        'meetings': [
                          {'id': 'first_id', 'name': 'meeting1',
                           'folder_id': 'folder1', 'slack_channel': 'channel-1'},
                          {'id': 'second_id', 'name': 'meeting2',
                           'folder_id': 'folder2', 'slack_channel': 'channel-2'}
                        ]}
    self.drive_config = {'credentials_json': '/tmp/credentials.json',
                         'client_secret_json': '/tmp/client_secrets.json'}
    self.internal_config = {'target_folder': '/tmp'}
