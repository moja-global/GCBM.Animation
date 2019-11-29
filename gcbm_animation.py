import os
import sys
import sqlite3
from argparse import ArgumentParser

if __name__ == "__main__":
    parser = ArgumentParser(description="Create GCBM results animations")
    parser.add_argument("study_area", type=os.path.abspath, help="Path to study area file for GCBM spatial input")
    parser.add_argument("spatial_results", type=os.path.abspath, help="Path to GCBM spatial output")
    parser.add_argument("db_results", type=os.path.abspath, help="Path to compiled GCBM results database")
    parser.add_argument("config", type=os.path.abspath, help="Path to animation config file")
    parser.add_argument("output_path", type=os.path.abspath, help="Directory to write animations to")
    args = parser.parse_args()

    for path in (args.study_area, args.spatial_results, args.db_results, args.config):
        if not os.path.exists(path):
            sys.exit(f"{path} not found.")
