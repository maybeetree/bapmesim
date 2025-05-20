pip install -e .
pip install pyinstaller
pip uninstall --yes typing

DEL /S /Q dist
RMDIR /S /Q dist

pyinstaller ^
	--hidden-import='PIL._tkinter_finder' ^
	--hidden-import=rasterio.abc ^
	--hidden-import=rasterio.control ^
	--hidden-import=rasterio.coords ^
	--hidden-import=rasterio.drivers ^
	--hidden-import=rasterio.dtypes ^
	--hidden-import=rasterio.enums ^
	--hidden-import=rasterio.env ^
	--hidden-import=rasterio.errors ^
	--hidden-import=rasterio.features ^
	--hidden-import=rasterio.fill ^
	--hidden-import=rasterio.io ^
	--hidden-import=rasterio.mask ^
	--hidden-import=rasterio.merge ^
	--hidden-import=rasterio.path ^
	--hidden-import=rasterio.plot ^
	--hidden-import=rasterio.profiles ^
	--hidden-import=rasterio.rpc ^
	--hidden-import=rasterio.sample ^
	--hidden-import=rasterio.session ^
	--hidden-import=rasterio.stack ^
	--hidden-import=rasterio.tools ^
	--hidden-import=rasterio.transform ^
	--hidden-import=rasterio.vrt ^
	--hidden-import=rasterio.warp ^
	--hidden-import=rasterio.windows ^
	--name bapmesim_tk ^
	--add-data=src/bapmesim_tk/res:bapmesim_tk/res ^
	--add-data=src/bapmesim_tk/sample_scripts:bapmesim_tk/sample_scripts ^
	--onefile ^
	src/bapmesim_tk/__main__.py 

:: No clue what safe.directory does
:: but doesn't work without it???

git -c safe.directory=* describe --tags --abbrev=0 > tagname.txt
SET /P tagname="" < tagname.txt
REN dist\bapmesim_tk.exe bapmesim_tk-%tagname: =%-windows.exe

