#!/usr/bin/env python3
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
import json

desc = """
Opens the given Zarr node, parses the contained OME-Zarr metadata,
and applies any coordinate transformations required
to convert the given coordinate array from the source coordinate system to the target.

Prints a JSON object like
'{"coordinates":[[1,2],[3.1,4.1],[5,6]]]}'
in the output system if successful.

Returns a nonzero exit code and may print a JSON object like
'{"message": "could not parse OME-Zarr metadata"}'
on failure.
"""
parser = ArgumentParser(
    prog="my_transformation_cli",
    description=desc,
    formatter_class=RawDescriptionHelpFormatter,
)
parser.add_argument(
    "path",
    metavar="PATH",
    type=Path,
    help="path to an OME-Zarr hierarchy on the file system with Scene metadata",
)
parser.add_argument(
    "source",
    metavar="SOURCE",
    help="name of a source coordinate system defined in the OME-Zarr Scene",
)
parser.add_argument(
    "target",
    metavar="TARGET",
    help="name of a target coordinate system defined in the OME-Zarr Scene",
)
parser.add_argument(
    "coordinates",
    metavar="COORDINATES",
    help="JSON-serialised array of coordinate arrays; e.g. 3 coordinates in 2D space '[[1,2],[3.1,4.1],[5,6]]'",
)

parser.parse_args()

print(
    json.dumps(
        {
            "coordinates": [
                [1, 2],
                [3.1, 4.1],
                [5, 6],
            ],
        },
        indent=2,
    )
)
