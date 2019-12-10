import gdal
import json
import logging
import os
import subprocess
import numpy as np
from gcbmanimation.util.tempfile import TempFileManager
from gcbmanimation.animator.frame import Frame

class Layer:
    '''
    Holds information about a layer to include in an animation. A layer applies
    to a single year, and the optional interpretation maps raster values to a
    single attribute value. If an interpretation is provided, any pixels not
    included are considered nodata.

    Arguments:
    'path' -- path to the layer file
    'year' -- the year the layer applies to
    'interpretation' -- optional attribute table for the raster; should be a
        dictionary of pixel value to interpretation, i.e. {1: "Wildfire"}
    '''

    def __init__(self, path, year, interpretation=None):
        self._path = path
        self._year = int(year)
        self._interpretation = interpretation
        self._info = None

    @property
    def interpretation(self):
        '''Gets the layer interpretation: dict of pixel value to string.'''
        return self._interpretation

    @property
    def has_interpretation(self):
        '''
        Checks if the layer has an interpretation (pixel values have meaning
        other than their literal numeric value).
        '''
        return self._interpretation is not None

    @property
    def path(self):
        '''Gets the layer's file path.'''
        return self._path

    @property
    def year(self):
        '''Gets the year the layer applies to.'''
        return self._year

    @property
    def info(self):
        '''Gets this layer's GDAL info dictionary, including min/max values.'''
        if not self._info:
            self._info = json.loads(gdal.Info(
                self._path, format="json", deserialize=False, computeMinMax=True).replace("nan", "0"))
        
        return self._info

    @property
    def min_max(self):
        '''Gets this layer's minimum and maximum pixel values.'''
        info = self.info
        if not info or "computedMin" not in info["bands"][0]:
            return (0, 0)

        return (info["bands"][0]["computedMin"], info["bands"][0]["computedMax"])

    @property
    def data_type(self):
        '''Gets this layer's data type.'''
        return self.info["bands"][0]["type"]

    @property
    def nodata_value(self):
        '''Gets this layer's nodata value in its correct Python type.'''
        value = self.info["bands"][0]["noDataValue"]
        dt = str(self.data_type).lower()
        if dt == "float32" or dt == "float" or dt == str(gdal.GDT_Float32):
            return float(value)
        else:
            return int(value)

    def get_histogram(self, min_value, max_value, buckets):
        '''Computes a histogram for this layer.'''
        raster = gdal.Open(self._path)
        band = raster.GetRasterBand(1)
        
        return band.GetHistogram(min=min_value, max=max_value, buckets=buckets)

    def reclassify(self, new_interpretation, nodata_value=0):
        '''
        Reclassifies a copy of this layer's pixel values according to a new interpretation.
        Any old interpretations not assigned a new pixel value will be set to nodata;
        for example, if the layer's original interpretation is {1: "Fire", 2: "Clearcut"},
        and the new interpretation is {3: "Fire"}, the original value 1 pixels will
        become 3, and the original value 2 pixels will become nodata.

        Arguments:
        'new_interpretation' -- dictionary of pixel value to interpreted value.
        'nodata_value' -- the new nodata pixel value.
        
        Returns a new reclassified Layer object.
        '''
        logging.info(f"Reclassifying {self._path}")
        raster = gdal.Open(self._path)
        band = raster.GetRasterBand(1)
        raster_data = band.ReadAsArray()

        uninterpreted_values = np.isin(raster_data, list(self._interpretation.keys()), invert=True)
        raster_data[uninterpreted_values] = nodata_value

        inverse_new_interpretation = {v: k for k, v in new_interpretation.items()}
        for original_pixel_value, interpreted_value in self._interpretation.items():
            new_pixel_value = inverse_new_interpretation[interpreted_value] \
                if interpreted_value in inverse_new_interpretation \
                else nodata_value

            if new_pixel_value == nodata_value:
                logging.info(f"  No new pixel value for {interpreted_value}: setting to nodata ({nodata_value})")

            raster_data[raster_data == original_pixel_value] = new_pixel_value

        output_path = TempFileManager.mktmp(suffix=".tif")
        self._save_as(raster_data, nodata_value, output_path)
        reclassified_layer = Layer(output_path, self._year, new_interpretation)

        return reclassified_layer

    def flatten(self):
        '''
        Flattens a copy of this layer: all non-nodata pixels become 1.
        Returns a new flattened Layer object.
        '''
        logging.info(f"Flattening {self._path}")
        raster = gdal.Open(self._path)
        band = raster.GetRasterBand(1)
        raster_data = band.ReadAsArray()
        raster_data[raster_data != self.nodata_value] = 1
        output_path = TempFileManager.mktmp(suffix=".tif")
        self._save_as(raster_data, self.nodata_value, output_path)
        flattened_layer = Layer(output_path, self.year)

        return flattened_layer

    def render(self, legend, bounding_box=None, transparent=True):
        '''
        Renders this layer into a colorized Frame according to the specified legend.

        Arguments:
        'legend' -- dictionary of pixel value (or tuple of min/max value range) to
            dictionary containing the color tuple (R, G, B) and label for the entry.
        'bounding_box' -- optional bounding box Layer; this layer will be cropped
            to the bounding box's minimum spatial extent and nodata pixels.
        'transparent' -- whether or not nodata and 0-value pixels should be
            transparent in the rendered Frame.
        
        Returns this layer as a colorized Frame object.
        '''
        with open(TempFileManager.mktmp(suffix=".txt"), "w") as color_table:
            color_table_path = color_table.name
            color_table.write(f"nv 255,255,255,{0 if transparent else 255}\n")
            color_table.write(f"0 255,255,255,{0 if transparent else 255}\n")

            near_zero_value = None
            near_zero_color = None
            for value, entry in legend.items():
                color_str = ",".join((f"{v}" for v in entry["color"]))
                if isinstance(value, tuple):
                    range_min, range_max = value
                    if range_min is not None:
                        color_table.write(f"{range_min} {color_str},255\n")
                    if range_max is not None:
                        color_table.write(f"{range_max} {color_str},255\n")
                    if (    range_min is not None and range_min < 0
                        and range_max is not None and range_max > 0
                    ):
                        near_zero_value = 0
                        near_zero_color = color_str
                    else:
                        min_val = min((abs(range_min), abs(range_max)))
                        if near_zero_value is None or min_val < near_zero_value:
                            near_zero_value = min_val
                            near_zero_color = color_str
                else:
                    color_table.write(f"{value} {color_str},255\n")
                    if near_zero_value is None or abs(value) < near_zero_value:
                        near_zero_value = abs(value)
                        near_zero_color = color_str
            
            # Guard the color entry closest to 0 against the 0/nodata color.
            color_table.write(f"{-1e-3} {near_zero_color},255\n{1e-3} {near_zero_color},255\n")

        working_layer = self if not bounding_box else bounding_box.crop(self)
        rendered_layer_path = TempFileManager.mktmp(suffix=".png")
        subprocess.run([
            "gdaldem",
            "color-relief",
            working_layer.path,
            color_table.name,
            rendered_layer_path,
            "-q",
            "-alpha",
            "-nearest_color_entry"])

        return Frame(self._year, rendered_layer_path)

    def _save_as(self, data, nodata_value, output_path):
        driver = gdal.GetDriverByName("GTiff")
        original_raster = gdal.Open(self._path)
        new_raster = driver.CreateCopy(output_path, original_raster, strict=0,
                                       options=["COMPRESS=DEFLATE", "BIGTIFF=YES"])

        band = new_raster.GetRasterBand(1)
        band.SetNoDataValue(nodata_value)
        band.WriteArray(data)
