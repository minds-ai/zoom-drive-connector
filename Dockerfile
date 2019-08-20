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
RUN python -m pip install zoom_drive_connector-1.1.0-py3-none-any.whl

# Create runuser and switch to it.
RUN useradd -ms /bin/false runuser
USER runuser

WORKDIR /home/runuser

# Set required environment variables.
ENV CONFIG="/conf/config.yaml"

# Run application.
ENTRYPOINT ["python"]
CMD ["-u", "main.py", "--noauth_local_webserver"]
