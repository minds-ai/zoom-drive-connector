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
import os


class TestSettingsBase(unittest.TestCase):
  def setUp(self):
    self.slack_config = {'channel_name': 'some_channel', 'key': 'random_key'}
    self.zoom_config = {'key': 'some_key',
                        'secret': 'some_secret',
                        'username': 'some@email.com',
                        'password': 's0mer4ndomv4lue!',
                        'delete': True,
                        'meetings': [
                          {'id': 'first_id', 'name': 'meeting1'},
                          {'id': 'second_id', 'name': 'meeting2'}
                        ]}
    self.drive_config = {'credentials_json': '/tmp/credentials.json',
                         'client_secret_json': '/tmp/client_secrets.json',
                         'folder_id': 'some_id'}
    self.internal_config = {'target_folder': os.getenv("TMPDIR", "/tmp")}
