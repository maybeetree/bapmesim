#!/bin/sh

apk add \
	python3 \
	python3-tkinter \
	font-terminus `# need at least one font` \
	\
	binutils `# for pyinstaller` \

#apk add -X https://dl-cdn.alpinelinux.org/alpine/edge/testing winetricks

