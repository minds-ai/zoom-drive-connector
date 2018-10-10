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