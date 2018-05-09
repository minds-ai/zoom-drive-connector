import os
import yaml


class APIConfigBase:
    def __init__(self, key: str, secret: str):
        """Initializes key and secret values.

        :param key: API client key.
        :param secret: API client secret.
        """
        self.key = key
        self.secret = secret

    def validate(self) -> bool:
        """Checks to see if key and secret values are not empty.

        :return: Secret and key have length of at least one.
        """
        return len(self.key) > 0 and len(self.secret) > 0


class SlackConfig(APIConfigBase):
    def __init__(self, key: str, channel: str):
        """Initializes key, secret, and notification channel option for Slack API. Passes `self.key` and
        `self.secret` to APIConfigBase.

        :param key: Slack API client key.
        :param secret: Slack API client secret.
        :param channel: Channel to report the upload in.
        """
        super().__init__(key, "")
        self.channel = channel

    @staticmethod
    def __class__():
        """Implements __class__ property.

        :return: Name of class
        """
        return 'Slack'
    
    
    
class ZoomConfig(APIConfigBase):
    def __init__(self, key: str, secret: str, username: str, password: str, delete: bool, meetings: list):
        """Initializes key, secret, and delete recording option for Zoom API. Passes `self.key` and
        `self.secret` to APIConfigBase.

        :param key: Zoom API client key.
        :param secret: Zoom API client secret.
        :param username: Username for the download user (email).
        :param password: Password for the download user.        
        :param delete: Option whether to delete recording or not.
        """
        super().__init__(key, secret)
        self.username = username
        self.password = password
        self.delete = delete
        self.meetings = meetings

    @staticmethod
    def __class__():
        """Implements __class__ property.

        :return: Name of class
        """
        return 'Zoom'


class DriveConfig(APIConfigBase):
    def __init__(self, key: str, secret: str, folder_id: str):
        """Initializes key, secret, and folder ID values for Google Drive API. Passes `self.key` and
        `self.secret` to APIConfigBase.

        :param key: Drive API client key.
        :param secret: Drive API client secret.
        :param folder_id: ID of folder to upload recordings to.
        """
        super().__init__(key, secret)
        self.folder_id = folder_id

    def validate(self) -> bool:
        """Checks to see if key, secret, and folder IDs are not empty.

        :return: Secret, key, and folder_id have length of at least one.
        """
        return super().validate() and len(self.folder_id) > 0

    @staticmethod
    def __class__():
        """Implements __class__ property.

        :return: Name of class
        """
        return 'Drive'


class SystemConfig:
    def __init__(self, target_folder: str, port: int):
        """Initializes download folder and port attributes.

        :param target_folder: folder to download temporary recordings.
        :param port: port on which to run the application.
        """
        self.target_folder = target_folder
        self.port = port

    def validate(self) -> bool:
        """Returns true if the target folder exists and the port number is greater than 1000.

        :return: True if the conditions listed about evaluate individually to true.
        """
        return os.path.isdir(self.target_folder) and self.port > 1000


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
                print('Position ({line}, {col})'.format(line=ye.problem_mark + 1,
                                                        col=ye.problem_mark + 1))

            raise SystemExit  # Crash program

    def __create_interfaces(self):
        """Loads configuration file using `self.__load_config` and generates tuple containing
        classes specific to each top level section.
        """
        conf_dict = self.__load_config()

        zoom = conf_dict["zoom"]
        print(zoom['meetings'])
        self.zoom_conf = ZoomConfig(zoom['key'], zoom['secret'], zoom['username'], zoom['password'], zoom['delete'], zoom['meetings'])
        drive = conf_dict["drive"]
        self.drive_conf = DriveConfig(drive['credentials_json'], drive['client_secret_json'], drive['folder_id'])
        slack = conf_dict["slack"]
        self.slack_conf = SlackConfig(slack["key"], slack["channel"])

        local = conf_dict["internals"]
        self.local_conf = SystemConfig(local['target_folder'], local['port'])


        conf_tuple = (self.zoom_conf, self.drive_conf) # local_conf slack_conf

        for c in conf_tuple:
            # Validate each item in `conf_tuple`.
            if not c.validate():
                raise RuntimeError('Validation of {} failed'.format(c.__class__()))

        self.config_tuple = conf_tuple
