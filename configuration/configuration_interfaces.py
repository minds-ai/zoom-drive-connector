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


class ZoomConfig(APIConfigBase):
    def __init__(self, key: str, secret: str, delete: bool):
        """Initializes key, secret, and delete recording option for Zoom API. Passes `self.key` and
        `self.secret` to APIConfigBase.

        :param key: Zoom API client key.
        :param secret: Zoom API client secret.
        :param delete: Option whether to delete recording or not.
        """
        super().__init__(key, secret)
        self.delete = delete


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


class ConfigInterface:
    def __init__(self, file: str):
        self.file = file
        self.config_dict = None

    def __load_config(self):
        try:
            with open(self.file, 'r') as f:
                self.config_dict = yaml.safe_load(f)
        except FileNotFoundError:
            print('YAML file {f} not found'.format(f=self.file))
            raise SystemExit  # Crash program
        except yaml.YAMLError as ye:
            print('Error in YAML file {f}'.format(f=self.file))

            # If the error can be identified, print it to the console.
            if hasattr(ye, 'problem_mark'):
                print('Position ({line}, {col})'.format(line=ye.problem_mark + 1,
                                                        col=ye.problem_mark + 1))

            raise SystemExit  # Crash program
