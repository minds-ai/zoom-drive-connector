# Makefile for building new Docker images that are properly versioned.
# Inspired by https://container-solutions.com/tagging-docker-images-the-right-way/
NAME	= $(shell git config --local --get remote.origin.url | awk -F '[:.]' '{ print $$3 }')
TAG		= $(shell git --no-pager log -1 --pretty=%H)
IMG		= ${NAME}:${TAG}
LATEST	= ${NAME}:latest

build:
	@docker build -t ${IMG} .
	@docker tag ${IMG} ${LATEST}