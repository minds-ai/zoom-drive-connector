# type: ignore # pylint: disable=no-member

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
from typing import Dict, Union, Any

import logging
import os
import yaml

log = logging.getLogger('app')


class APIConfigBase:
  def __init__(self, settings_dict: Dict):
    """Initializes key and secret values.

    :param settings_dict: dictionary of settings corresponding to specific service.
    """
    self.settings_dict = settings_dict

  def validate(self) -> bool:
    """Dummy validation method.

    :return: Always returns true.
    """
    return True

  def __getattr__(self, item) -> Union[str, int]:
    """Allows for dot operator access to anything in `settings_dict`.

    :param item: name of attribute to return from `settings_dict`.
    :return: value of attribute in dictionary. Either string or integer.
    """
    return self.settings_dict[item]

  @classmethod
  def factory_registrar(cls, name):
    """Returns true if the current class is the proper registrar for the corresponding config class.

    :param name: name of class that should be registered.
    :return: if __class__ matched the passed in class name.
    """
    return name == cls._classname


class SlackConfig(APIConfigBase):
  _classname = 'slack'


class ZoomConfig(APIConfigBase):
  _classname = 'zoom'


class DriveConfig(APIConfigBase):
  _classname = 'drive'

  def validate(self) -> bool:
    """Checks to see if all parameters are valid.

    :return: Checks to make sure that the secret file exists and the folder ID is not empty or
    otherwise invalid.
    """
    files_exist = os.path.exists(self.settings_dict['client_secret_json'])
    return files_exist


class SystemConfig(APIConfigBase):
  _classname = 'internals'

  def validate(self) -> bool:
    """Returns true if the target folder exists.

    :return: True if the condition listed about evaluates to true.
    """
    return os.path.isdir(self.settings_dict['target_folder'])


class ConfigInterface:
  def __init__(self, file: str):
    """Initializes and loads configuration file to Python object.
    """
    self.file = file
    self.configuration_dict: Dict = dict()

    # Load configuration
    self.__interface_factory()

  def __load_config(self) -> Dict[str, Any]:
    """Loads YAML configuration file to Python dictionary. Does some basic error checking to help
    with debugging bad configuration files.
    """
    try:
      with open(self.file, 'r') as f:
        return yaml.safe_load(f)
    except yaml.YAMLError as ye:
      log.log(logging.ERROR, f'Error in YAML file {self.file}')

      # If the error can be identified, print it to the console.
      if hasattr(ye, 'problem_mark'):
        log.log(logging.INFO, f'Error at position ({ye.problem_mark.line + 1}, '
                              f'{ye.problem_mark.column + 1})')

      raise SystemExit  # Crash program

  def __interface_factory(self):
    """Loads configuration file using `self.__load_config` and iterates through each top-level key
    and instantiates the corresponding configuration class depending on the name of the key. Each
    class then has its validation method run to check for any errors.
    """
    dict_from_yaml = self.__load_config()

    # Iterate through all keys and their corresponding values.
    for key, value in dict_from_yaml.items():
      # Iterator for subclasses of `APIConfigBase`.
      for cls in APIConfigBase.__subclasses__():
        if cls.factory_registrar(key):
          self.configuration_dict[key] = cls(value)

    # Run validation for each item in the dictionary.
    for value in self.configuration_dict.values():
      if not value.validate():
        raise RuntimeError(f'Configuration for section {value.__class__} failed validation step.')

  def __getattr__(self, item) -> APIConfigBase:
    """Returns the configuration class corresponding to given name. Allows "dot" access to items
    in the configuration_dict.

    :param item: name of the key in `configuration_dict`.
    :return: the value corresponding to the key specified by the parameter `item`.
    """
    return self.configuration_dict[item]
