from requests import PreparedRequest


class ZoomAPIException(Exception):
  def __init__(self, status_code: int, name: str, method: PreparedRequest, message: str):
    """Initializes container for holding HTTP status information.

    :param status_code: HTTP status code.
    :param name: HTTP status name.
    :param method: HTTP method used.
    :param message: Exception message/reason.
    """
    super(ZoomAPIException, self).__init__()
    self.status_code = status_code
    self.name = name
    self.method = method
    self.message = message

  def __str__(self) -> str:
    """Returns printable string with formatted exception message.

    Usage: print(ZoomAPIException)
    """
    return 'HTTP_STATUS: {c}-{n}, {m}'.format(c=self.status_code, n=self.name, m=self.message)

  def __repr__(self) -> str:
    """Returns class type when repr method called.
    """
    return 'ZoomAPIException()'

  @property
  def http_method(self):
    """Returns request method.
    """
    return self.method.method if self.method else None
