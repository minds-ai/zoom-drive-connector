FROM ubuntu:latest
LABEL MAINTAINER.1="Jeroen Bedorf <jeroen@minds.ai>" \
      MAINTAINER.2="Nick Pleatsikas <nick@minds.ai>"

# Update the system
RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

ENTRYPOINT ["python3"]

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["-u", "main.py", "--noauth_local_webserver"]
