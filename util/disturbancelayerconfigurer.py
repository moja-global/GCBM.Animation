import os
import json

class DisturbanceLayerConfigurer:
    '''
    Scans a study_area.json file for disturbance layers, collecting the final
    *_moja.tif files along with their tiled metadata (disturbance type and year),
    splitting them into multiple instances if more than one year is present in a
    file.
    '''

    def __init__(self):
        pass

    def configure(self, study_area_path):
        pass
