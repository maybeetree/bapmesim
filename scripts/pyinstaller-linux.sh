#!/bin/sh

#if ! command -v zstd
#	if command -v apk
#	then
#		apk add zstd 
#	elif command -v xbps-install
#	then
#		xbps-install -Syu zstd
#	else
#		echo "No clue how to install zstd." >&2
#		echo "Will fail to make archive." >&2
#	fi
#fi

if ! command -v objdump
then
	if command -v apk
	then
		apk add binutils 
	elif command -v xbps-install
	then
		xbps-install -Syu binutils
	else
		echo "No clue how to install binutils." >&2
		echo "Pyisntaller will not work." >&2
	fi
fi

if ! (printf '%s\n' "$(pip freeze)" | grep bapmesim_tk)
then
	pip install -e .
fi

if ! (printf '%s\n' "$(pip freeze)" | grep pyinstaller)
then
	pip install pyinstaller
fi

if (printf '%s\n' "$(pip freeze)" | grep typing)
then
	pip uninstall --yes typing
fi

rm -rf dist

pyinstaller \
	--hidden-import='PIL._tkinter_finder' \
	--hidden-import=rasterio.abc \
	--hidden-import=rasterio.control \
	--hidden-import=rasterio.coords \
	--hidden-import=rasterio.drivers \
	--hidden-import=rasterio.dtypes \
	--hidden-import=rasterio.enums \
	--hidden-import=rasterio.env \
	--hidden-import=rasterio.errors \
	--hidden-import=rasterio.features \
	--hidden-import=rasterio.fill \
	--hidden-import=rasterio.io \
	--hidden-import=rasterio.mask \
	--hidden-import=rasterio.merge \
	--hidden-import=rasterio.path \
	--hidden-import=rasterio.plot \
	--hidden-import=rasterio.profiles \
	--hidden-import=rasterio.rpc \
	--hidden-import=rasterio.sample \
	--hidden-import=rasterio.session \
	--hidden-import=rasterio.stack \
	--hidden-import=rasterio.tools \
	--hidden-import=rasterio.transform \
	--hidden-import=rasterio.vrt \
	--hidden-import=rasterio.warp \
	--hidden-import=rasterio.windows \
	--name bapmesim_tk \
	--add-data=src/bapmesim_tk/res:bapmesim_tk/res \
	--add-data=src/bapmesim_tk/sample_scripts:bapmesim_tk/sample_scripts \
	`#--onedir ` \
	--onefile \
	src/bapmesim_tk/__main__.py 

tagname=$(git describe --tags --abbrev=0)
mv dist/bapmesim_tk "dist/bapmesim_tk-${tagname}-linux"

#cd dist
#
#tar c "bapmesim_tk-${tagname}-linux" - |
#	zstd --long --ultra --threads=0 -22 > 
#	"bapmesim_tk-${tagname}-linux.tar.zst"

