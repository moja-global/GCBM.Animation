import psutil

gdal_memory_limit = int(psutil.virtual_memory().available * 0.75)
gdal_creation_options = ["BIGTIFF=YES", "TILED=YES", "COMPRESS=ZSTD", "ZSTD_LEVEL=1"]
