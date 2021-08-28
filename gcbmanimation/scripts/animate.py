import os
import sys
import sqlite3
import json
import logging
from glob import glob
from argparse import ArgumentParser
from gcbmanimation.util.disturbancelayerconfigurer import DisturbanceLayerConfigurer
from gcbmanimation.provider.sqlitegcbmresultsprovider import SqliteGcbmResultsProvider
from gcbmanimation.provider.spatialgcbmresultsprovider import SpatialGcbmResultsProvider
from gcbmanimation.indicator.indicator import Indicator
from gcbmanimation.layer.units import Units
from gcbmanimation.animator.animator import Animator
from gcbmanimation.layer.boundingbox import BoundingBox
from gcbmanimation.color.quantilecolorizer import QuantileColorizer
from gcbmanimation.util.tempfile import TempFileManager


def find_units(units_str):
    try:
        return Units[units_str]
    except:
        return Units.Tc


def cli():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
    TempFileManager.delete_on_exit()

    parser = ArgumentParser(description="Create GCBM results animations")
    parser.add_argument(
        "study_area",
        type=os.path.abspath,
        help="Path to study area file for GCBM spatial input",
    )
    parser.add_argument(
        "spatial_results", type=os.path.abspath, help="Path to GCBM spatial output"
    )
    parser.add_argument(
        "config", type=os.path.abspath, help="Path to animation config file"
    )
    parser.add_argument(
        "output_path", type=os.path.abspath, help="Directory to write animations to"
    )
    parser.add_argument(
        "--db_results",
        type=os.path.abspath,
        help="Path to compiled GCBM results database",
    )
    parser.add_argument(
        "--bounding_box",
        type=os.path.abspath,
        help="Bounding box defining animation area",
    )
    args = parser.parse_args()

    for path in filter(
        lambda fn: fn,
        (args.study_area, args.spatial_results, args.db_results, args.config),
    ):
        if not os.path.exists(path):
            sys.exit(f"{path} not found.")

    bounding_box_file = args.bounding_box
    if not bounding_box_file:
        # Try to find a suitable bounding box: the tiler bounding box is usually
        # the only tiff file in the study area directory without "moja" in its name;
        # if that isn't found, use the first tiff file in the study area dir.
        study_area_dir = os.path.dirname(args.study_area)
        bounding_box_candidates = glob(os.path.join(study_area_dir, "*.tiff"))
        bounding_box_file = next(
            filter(lambda tiff: "moja" not in tiff, bounding_box_candidates), None
        )
        if not bounding_box_file:
            bounding_box_file = bounding_box_candidates[0]

    logging.info(f"Using bounding box: {bounding_box_file}")
    bounding_box = BoundingBox(bounding_box_file)

    disturbance_configurer = DisturbanceLayerConfigurer()
    disturbance_layers = disturbance_configurer.configure(args.study_area)

    indicators = []
    for indicator_config in json.load(open(args.config, "rb")):
        graph_units = (
            find_units(indicator_config["graph_units"])
            if "graph_units" in indicator_config
            else Units.Tc
        )
        map_units = (
            find_units(indicator_config["map_units"])
            if "map_units" in indicator_config
            else Units.TcPerHa
        )

        output_file_pattern = indicator_config["file_pattern"]
        output_file_units = Units.TcPerHa
        if isinstance(output_file_pattern, list):
            output_file_pattern, output_file_units = output_file_pattern

        output_file_pattern = os.path.join(args.spatial_results, output_file_pattern)

        results_provider = (
            SqliteGcbmResultsProvider(args.db_results)
            if args.db_results and not args.bounding_box
            else SpatialGcbmResultsProvider(output_file_pattern)
        )

        indicators.append(
            Indicator(
                indicator_config["database_indicator"],
                output_file_pattern,
                results_provider,
                {"indicator": indicator_config["database_indicator"]},
                indicator_config.get("title"),
                graph_units,
                map_units,
                colorizer=QuantileColorizer(
                    palette=indicator_config.get("palette"),
                    negative_palette=indicator_config.get("negative_palette"),
                ),
            )
        )

    animator = Animator(disturbance_layers, indicators, args.output_path)
    animator.render(bounding_box)


if __name__ == "__main__":
    cli()
