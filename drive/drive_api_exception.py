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
