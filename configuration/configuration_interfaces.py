import os
import yaml

from typing import Union


class APIConfigBase:
  def __init__(self, settings_dict: dict):
    """Initializes key and secret values.

    :param settings_dict: dictionary of settings corresponding to specific service.
    """
    self.settings_dict = settings_dict

  def __getattr__(self, item) -> Union[str, int]:
    """Allows for dot operator access to anything in `settings_dict`.

    :param item: name of attribute to return from `settings_dict`.
    :return: value of attribute in dictionary. Either string or integer.
    """
    return self.settings_dict[item]


class SlackConfig(APIConfigBase):
  @staticmethod
  def __class__():
    """Implements __class__ property.

    :return: Name of class
    """
    return 'slack'


class ZoomConfig(APIConfigBase):
  @staticmethod
  def __class__():
    """Implements __class__ property.

        :return: Name of class
        """
    return 'Zoom'


class DriveConfig(APIConfigBase):
  def validate(self) -> bool:
    """Checks to see if all parameters are valid.

    :return: Checks to make sure that the secret file exists and the folder ID is not empty or
    otherwise invalid.
    """
    files_exist = os.path.exists(self.settings_dict['secret'])
    valid_folder_id = self.settings_dict['secret'] is not None \
                      and len(self.settings_dict['dict']) > 0

    return files_exist and valid_folder_id

  @staticmethod
  def __class__():
    """Implements __class__ property.

    :return: Name of class
    """
    return 'drive'


class SystemConfig(APIConfigBase):
  def validate(self) -> bool:
    """Returns true if the target folder exists and the port number is greater than 1000.

    :return: True if the conditions listed about evaluate individually to true.
    """
    return os.path.isdir(self.settings_dict['target_folder']) and self.settings_dict['port'] > 1000

  @staticmethod
  def __class__():
    return 'internal'


class ConfigInterface:
  def __init__(self, file: str):
    """Initializes and loads configuration file to Python object.
    """
    self.file = file
    self.config_tuple = None

    # Load configuration
    self.__create_interfaces()

  def __load_config(self) -> dict:
    """Loads YAML configuration file to Python object. Does some basic error checking to help
    with debugging bad configuration files.
    """
    try:
      with open(self.file, 'r') as f:
        return yaml.safe_load(f)
    except yaml.YAMLError as ye:
      print('Error in YAML file {f}'.format(f=self.file))

      # If the error can be identified, print it to the console.
      if hasattr(ye, 'problem_mark'):
        print('Position ({line}, {col})'.format(line=ye.problem_mark + 1, col=ye.problem_mark + 1))

      raise SystemExit  # Crash program

  def __create_interfaces(self):
    """Loads configuration file using `self.__load_config` and generates tuple containing
    classes specific to each top level section.
    """
    conf_dict = self.__load_config()

    self.zoom_conf = ZoomConfig(conf_dict['zoom'])
    self.drive_conf = DriveConfig(conf_dict['drive'])
    self.slack_conf = SlackConfig(conf_dict['slack'])
    self.local_conf = SystemConfig(conf_dict['internals'])

    conf_tuple = (self.zoom_conf, self.drive_conf, self.slack_conf, self.local_conf)

    for c in conf_tuple:
      # Validate each item in `conf_tuple`.
      if not c.validate():
        raise RuntimeError('Validation of {} failed'.format(c.__class__()))

    self.config_tuple = conf_tuple
