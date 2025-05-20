#!/bin/sh

cd /venv/lib/python3.13/site-packages/rasterio &&
	printf '%s\n' [a-z]*.py |
	sed 's/\.py$//g;s/^/--hidden-import=rasterio./'

