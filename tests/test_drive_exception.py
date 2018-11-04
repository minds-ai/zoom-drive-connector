import unittest

from drive import DriveAPIException


class TestDriveAPIException(unittest.TestCase):
  def test_throw_exception(self):
    with self.assertRaises(DriveAPIException):
      raise DriveAPIException('Test', 'Test reason')

  def test_str_method(self):
    self.assertEqual(str(DriveAPIException('Test', 'Test reason.')),
                     'DRIVE_API_FAILURE: Test, Test reason.')

  def test_repr_methpd(self):
    self.assertEqual(repr(DriveAPIException('Test', 'Test reason')), 'DriveAPIException()')
