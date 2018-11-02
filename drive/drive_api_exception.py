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


class DriveAPIException(Exception):
  def __init__(self, name: str, reason: str):
    """Initializes object for containing information about an exception or error with the Google
    Drive API or its defined interface.

    :param name: Name of the error.
    :param reason: Reason for error.
    """
    super(DriveAPIException, self).__init__()
    self.name = name
    self.reason = reason

  def __str__(self) -> str:
    """Returns formatted message containing information about the exception. This should be human
    readable.

    :return: String with exception contents.
    """
    return 'DRIVE_API_FAILURE: {n}, {r}'.format(n=self.name, r=self.reason)

  def __repr__(self) -> str:
    """Returns name of exception class.

    :return: name of exception class.
    """
    return 'DriveAPIException()'
