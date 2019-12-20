import os
import json
from gcbmanimation.layer.layer import Layer
from gcbmanimation.layer.layercollection import LayerCollection

class DisturbanceLayerConfigurer:
    '''
    Scans a study_area.json file for disturbance layers, collecting the final
    *_moja.tif files along with their tiled metadata (disturbance type and year),
    splitting them into multiple instances if more than one year is present in a
    file.

    Arguments:
    'palette' -- the color palette to use for the layer collection - can be the
        name of any seaborn palette (deep, muted, bright, pastel, dark, colorblind,
        hls, husl) or matplotlib colormap. To find matplotlib colormaps:
        from matplotlib import cm; dir(cm)
    '''
    def __init__(self, palette="hls"):
        self._palette = palette

    def configure(self, study_area_path):
        '''
        Scans the specified study area JSON file for disturbance layers and returns
        a LayerCollection containing them.

        Arguments:
        'study_area_path' -- the path to the study area file to scan.
        '''
        if not os.path.exists(study_area_path):
            raise IOError(f"{study_area_path} not found.")

        study_area = json.load(open(study_area_path, "rb"))
        layers = study_area["layers"]
        disturbance_layers = [layer for layer in study_area["layers"]
                              if "disturbance" in layer.get("tags", [])]
        
        layer_collection = LayerCollection(palette=self._palette)
        study_area_dir = os.path.dirname(study_area_path)
        for layer in disturbance_layers:
            layer_tif = os.path.join(study_area_dir, f"{layer['name']}_moja.tiff")
            layer_metadata_file = os.path.join(
                study_area_dir,
                f"{layer['name']}_moja", f"{layer['name']}_moja.json")

            if not self._files_exist(layer_tif, layer_metadata_file):
                continue

            layer_attribute_table = json.load(open(layer_metadata_file, "rb")).get("attributes")
            if not layer_attribute_table:
                continue
            
            # If the layer contains multiple years, split it up by year.
            disturbance_years = {attr["year"] for attr in layer_attribute_table.values()}
            for year in disturbance_years:
                interpretation = {
                    int(raster_value): attr["disturbance_type"]
                    for raster_value, attr in layer_attribute_table.items()
                    if attr["year"] == year}

                layer_collection.append(Layer(layer_tif, year, interpretation))

        return layer_collection

    def _files_exist(self, *paths):
        return all((os.path.exists(path) for path in paths))
