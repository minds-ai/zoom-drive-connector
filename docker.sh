#!/usr/bin/env bash

docker build -t zoom_download .
docker run zoom_download