import os
import shutil
from glob import glob
from layer.layercollection import LayerCollection
from layer.layer import Layer
from layer.boundingbox import BoundingBox
from util.disturbancelayerconfigurer import DisturbanceLayerConfigurer
from database.sqlitegcbmresultsdatabase import SqliteGcbmResultsDatabase
from animator.indicator import Indicator
from animator.indicator import Units
from animator.legend import Legend
from animator.animator import Animator

# Test a plain old LayerCollection - bounding box is the first layer found.
layers = LayerCollection(palette="Reds")
bbox = None
for layer_path in glob(r"C:\Projects\Standalone_Template\processed_output\spatial\NPP*.tiff"):
    year = os.path.splitext(layer_path)[0][-4:]
    layer = Layer(layer_path, year)
    layers.append(layer)
    if not bbox:
        bbox = BoundingBox(layer_path)

# Render and save the output for viewing.
indicator_frames, indicator_legend = layers.render(bounding_box=bbox, start_year=2010, end_year=2020)
for rendered_layer in indicator_frames:
    shutil.copyfile(rendered_layer.path, rf"c:\tmp\indicator_{rendered_layer.year}.png")

# Test a DisturbanceLayerConfigurer.
disturbance_configurer = DisturbanceLayerConfigurer()
disturbance_layers = disturbance_configurer.configure(r"C:\Projects\Standalone_Template\layers\tiled\study_area.json")

# Render using the bounding box from earlier and save the output for viewing.
disturbance_frames, disturbance_legend = disturbance_layers.render(bounding_box=bbox, start_year=2010, end_year=2020)
for rendered_layer in disturbance_frames:
    shutil.copyfile(rendered_layer.path, rf"c:\tmp\disturbance_{rendered_layer.year}.png")

# Test an Indioator.
results_db = SqliteGcbmResultsDatabase(r"C:\Projects\Standalone_Template\processed_output\compiled_gcbm_output.db")
indicator = Indicator(results_db, "NPP", r"C:\Projects\Standalone_Template\processed_output\spatial\NPP*.tiff", graph_units=Units.Ktc, palette="Greens")

# Render using the bounding box from earlier and save the output for viewing.
for frame in indicator.render_map_frames(bounding_box=bbox)[0]:
    shutil.copyfile(frame.path, rf"c:\tmp\{indicator.title}_map_{frame.year}.png")

for frame in indicator.render_graph_frames():
    shutil.copyfile(frame.path, rf"c:\tmp\{indicator.title}_graph_{frame.year}.png")

# Test generating a legend.
legend = Legend({"Indicator": indicator_legend, "Disturbances": disturbance_legend})
legend_frame = legend.render()
shutil.copyfile(legend_frame.path, rf"c:\tmp\legend.png")

# Test animator.
animator = Animator(disturbance_layers, [indicator], r"c:\tmp")
animator.render(bbox, 2010, 2020)
