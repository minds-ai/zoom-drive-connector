# Copyright 2019 Minds.ai, Inc. All Rights Reserved.
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
FROM python:3.7.4-slim-buster AS base
FROM base AS build

LABEL MAINTAINER.1="Jeroen Bedorf <jeroen@minds.ai>" \
      MAINTAINER.2="Nick Pleatsikas <nick@minds.ai>"

# Copy project files into build container.
WORKDIR /build
COPY . /build

# Create python wheel.
RUN python setup.py bdist_wheel

# Main container. This is where the application will be installed and run.
FROM base

# Create required volumes.
VOLUME /conf

# Copy wheel from build container into current container and install.
WORKDIR /dist
COPY --from=build /build/dist /dist
RUN python -m pip install zoom_drive_connector-*-py3-none-any.whl

# Create runuser and switch to it.
RUN useradd -ms /bin/false runuser
USER runuser

WORKDIR /home/runuser

# Set required environment variables.
ENV CONFIG="/conf/config.yaml"

# Run application.
ENTRYPOINT ["python"]
CMD ["-u", "-m", "zoom_drive_connector", "--noauth_local_webserver"]
