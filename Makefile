# Copyright 2018 Minds.ai, Inc. All Rights Reserved.
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
#
# Makefile for building new Docker images that are properly versioned.
# Inspired by https://container-solutions.com/tagging-docker-images-the-right-way/
GIT_URL = $(shell git config --local --get remote.origin.url)

ifneq (,$(findstring https, $(GIT_URL)))
	# Cloned via HTTPS
	NAME = $(shell echo ${GIT_URL} | awk -F '[/.]' '{print $$5"/"$$6}')
else
	# Cloned via SSH
	NAME = $(shell echo ${GIT_URL} | awk -F '[:.]' '{print $$3}')
endif

TAG		= $(shell git --no-pager log -1 --pretty=%H)
IMG		= ${NAME}:${TAG}
LATEST	= ${NAME}:latest

build:
	@docker build -t ${IMG} .
	@docker tag ${IMG} ${LATEST}
