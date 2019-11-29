import os
import shutil
from layer.layercollection import LayerCollection
from layer.layer import Layer
from layer.boundingbox import BoundingBox
from glob import glob

layers = LayerCollection(palette="Reds")
bbox = None
for layer_path in glob(r"C:\Projects\Standalone_Template\processed_output\spatial\Bio_To_DOM_From_Disturbances*.tiff"):
    year = os.path.splitext(layer_path)[0][-4:]
    layer = Layer(layer_path, year)
    layers.append(layer)
    if not bbox:
        bbox = BoundingBox(layer_path)

for rendered_layer in layers.render(bounding_box=bbox, start_year=1990, end_year=2020)[0]:
    shutil.copyfile(rendered_layer.path, rf"c:\tmp\{rendered_layer.year}.png")
