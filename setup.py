from setuptools import setup, find_packages
from os import path

# Read the contents of the README into the long_description field.
current_directory = path.abspath(path.dirname(__file__))
with open(path.join(current_directory, 'README.md'), encoding='utf-8') as f:
  long_description = f.read()

setup(
  name='zoom-drive-connector',
  version='1.4',
  packages=find_packages(exclude=['tests']),
  url='https://github.com/minds-ai/zoom-drive-connector',
  license='Apache 2.0',
  author='Nick Pleatsikas, Jeroen Bédorf',
  author_email='nick@minds.ai, jeroen@minds.ai',
  # Package description.
  description='Automatically copies recordings from Zoom to Google Drive.',
  long_description=long_description,
  long_description_content_type='text/markdown',
  # Package requirements.
  install_requires=[
    'pyjwt==1.5.3',
    'pyyaml>=5.1',
    'slackclient==1.2.1',
    'schedule==0.5.0',
    'google-api-python-client==2.10.0',
    'google-auth-httplib2==0.1.0',
    'google-auth-oauthlib==0.4.4',
  ],
  python_requires='>=3.5, <4',
  # Development requirements.
  extras_require={
    'test': ['tox', 'mypy', 'pylint', 'pycodestyle', 'responses']
  },
  # Application entrypoint.
  entry_points={
    'console_scripts': [
      'zoom-drive-connector=zoom_drive_connector:__main__.main'
    ]
  }
)
