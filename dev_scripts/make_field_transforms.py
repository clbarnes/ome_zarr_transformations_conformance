#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "numpy>=2.4.6",
#     "zarr>=3.2.1",
#     "tomli_w",
# ]
# ///
import sys
from pathlib import Path
import shutil
import json

import zarr
import numpy as np
import tomli_w

case_dir = Path(__file__).resolve().parent.parent / "cases"


def make_displacements():
    name = "displacements_constant"
    case_path = case_dir / f"{name}.ome.zarr"
    if case_path.exists():
        shutil.rmtree(case_path)
    case_path.mkdir()

    scene = {
        "coordinateSystems": [
            {
                "name": "input",
                "axes": [
                    {"name": "y", "type": "space"},
                    {"name": "x", "type": "space"},
                ],
            },
            {
                "name": "output",
                "axes": [
                    {"name": "y", "type": "space"},
                    {"name": "x", "type": "space"},
                ],
            },
        ],
        "coordinateTransformations": [
            {
                "name": "inputToOutput",
                "type": "displacements",
                "input": {"name": "input"},
                "output": {"name": "output"},
                "path": "coordinateTransformations/inputToOutput",
                "interpolation": "linear",
            }
        ],
    }
    zarr_json = {
        "zarr_format": 3,
        "node_type": "group",
        "attributes": {"ome": {"version": "0.6", "scene": scene}},
    }
    (case_path / "zarr.json").write_text(json.dumps(zarr_json, indent=2) + "\n")

    # 4x4 constant displacement field: [dy, dx] = [1.0, 2.0] everywhere
    # Array shape (4, 4, 2): N=2 input axes + component axis of length N=2
    grid = 4
    field = np.zeros((grid, grid, 2), dtype="float32")
    field[..., 0] = 1.0
    field[..., 1] = 2.0

    root = zarr.open_group(case_path)
    ct_grp = root.create_group("coordinateTransformations")
    arr = ct_grp.create_array("inputToOutput", data=field, compressors=None)
    # Array-level OME metadata: axes match input space + displacement component axis
    # Identity coordinateTransformation means array indices == input space coordinates
    arr.attrs["ome"] = {
        "coordinateSystems": [
            {
                "name": "inputToOutput",
                "axes": [
                    {"name": "y", "type": "space"},
                    {"name": "x", "type": "space"},
                    {"name": "d", "type": "displacement"},
                ],
            }
        ],
        "coordinateTransformations": [
            {"type": "identity", "output": {"name": "inputToOutput"}}
        ],
    }

    # All source points are integer-valued and within the 4x4 grid,
    # so no interpolation is needed: output = input + [1, 2]
    conformance = {
        "description": "Constant 2D displacement field shifting all points by (1, 2).",
        "should_error": False,
        "absolute_tolerance": 1e-6,
        "relative_tolerance": 1e-3,
        "source": {
            "name": "input",
            "coordinates": [[0.0, 0.0], [1.0, 1.0], [2.0, 3.0], [3.0, 0.0]],
        },
        "target": {
            "name": "output",
            "coordinates": [[1.0, 2.0], [2.0, 3.0], [3.0, 5.0], [4.0, 2.0]],
        },
    }
    (case_path / "conformance.toml").write_text(tomli_w.dumps(conformance))


def make_coordinates_1d():
    name = "coordinates_1d"
    case_path = case_dir / f"{name}.ome.zarr"
    if case_path.exists():
        shutil.rmtree(case_path)
    case_path.mkdir()

    scene = {
        "coordinateSystems": [
            {"name": "input", "axes": [{"name": "i", "type": "space"}]},
            {"name": "output", "axes": [{"name": "x", "type": "space"}]},
        ],
        "coordinateTransformations": [
            {
                "name": "inputToOutput",
                "type": "coordinates",
                "input": {"name": "input"},
                "output": {"name": "output"},
                "path": "coordinateTransformations/inputToOutput",
                "interpolation": "linear",
            }
        ],
    }
    zarr_json = {
        "zarr_format": 3,
        "node_type": "group",
        "attributes": {"ome": {"version": "0.6", "scene": scene}},
    }
    (case_path / "zarr.json").write_text(json.dumps(zarr_json, indent=2) + "\n")

    # 5 grid points: x[i] = i * 2.0
    # Array shape (5, 1): N=1 input axis + component axis of length M=1
    field = (np.arange(5, dtype="float32") ** 2).reshape(5, 1)

    root = zarr.open_group(case_path)
    ct_grp = root.create_group("coordinateTransformations")
    arr = ct_grp.create_array("inputToOutput", data=field, compressors=None)
    # Array-level OME metadata: input axis + coordinate component axis
    # Identity coordinateTransformation means array index == input space coordinate
    arr.attrs["ome"] = {
        "coordinateSystems": [
            {
                "name": "inputToOutput",
                "axes": [
                    {"name": "i", "type": "space"},
                    {"name": "c", "type": "coordinate"},
                ],
            }
        ],
        "coordinateTransformations": [
            {"type": "identity", "output": {"name": "inputToOutput"}}
        ],
    }

    # Integer source indices within [0, 4]; field value at i is x = i ** 2
    conformance = {
        "description": "1D coordinate field mapping index to physical space (x = i ** 2).",
        "should_error": False,
        "absolute_tolerance": 1e-6,
        "relative_tolerance": 1e-3,
        "source": {
            "name": "input",
            "coordinates": [
                [0.0],
                [0.9],
                [1.0],
                [1.5],
                [2.0],
                [2.5],
                [3.0],
                [3.3],
                [4.0],
            ],
        },
        "target": {
            "name": "output",
            "coordinates": [
                [0.0],
                [0.9],
                [1.0],
                [2.5],
                [4.0],
                [6.5],
                [9.0],
                [11.1],
                [16.0],
            ],
        },
    }
    (case_path / "conformance.toml").write_text(tomli_w.dumps(conformance))


def make_coordinates_2d_3d():
    name = "coordinates_2d-3d"
    case_path = case_dir / f"{name}.ome.zarr"
    if case_path.exists():
        shutil.rmtree(case_path)
    case_path.mkdir()

    scene = {
        "coordinateSystems": [
            {
                "name": "input",
                "axes": [
                    {"name": "v", "type": "space"},
                    {"name": "u", "type": "space"},
                ],
            },
            {
                "name": "output",
                "axes": [
                    {"name": "z", "type": "space"},
                    {"name": "y", "type": "space"},
                    {"name": "x", "type": "space"},
                ],
            },
        ],
        "coordinateTransformations": [
            {
                "name": "inputToOutput",
                "type": "coordinates",
                "input": {"name": "input"},
                "output": {"name": "output"},
                "path": "coordinateTransformations/inputToOutput",
                "interpolation": "nearest",
            }
        ],
    }
    zarr_json = {
        "zarr_format": 3,
        "node_type": "group",
        "attributes": {"ome": {"version": "0.6", "scene": scene}},
    }
    (case_path / "zarr.json").write_text(json.dumps(zarr_json, indent=2) + "\n")

    # 4x4 grid; z=v², y=v+u, x=u² — all integer-valued at integer indices so no interpolation needed
    grid = 4
    v_idx = np.arange(grid, dtype="float32")
    u_idx = np.arange(grid, dtype="float32")
    vv, uu = np.meshgrid(v_idx, u_idx, indexing="ij")
    field = np.stack([vv**2, vv + uu, uu**2], axis=-1)

    root = zarr.open_group(case_path)
    ct_grp = root.create_group("coordinateTransformations")
    arr = ct_grp.create_array("inputToOutput", data=field, compressors=None)
    # Array-level OME metadata: input axis + coordinate component axis
    # Identity coordinateTransformation means array index == input space coordinate
    arr.attrs["ome"] = {
        "coordinateSystems": [
            {
                "name": "inputToOutput",
                "axes": [
                    {"name": "v", "type": "space"},
                    {"name": "u", "type": "space"},
                    {"name": "c", "type": "coordinate"},
                ],
            }
        ],
        "coordinateTransformations": [
            {"type": "identity", "output": {"name": "inputToOutput"}}
        ],
    }

    # Integer-valued source indices within the 4x4 grid; z=v², y=v+u, x=u²
    conformance = {
        "description": "2D coordinate field mapping (v, u) indices to 3D physical space (z=v², y=v+u, x=u²), with nearest interolation.",
        "should_error": False,
        "absolute_tolerance": 1e-6,
        "relative_tolerance": 1e-3,
        "source": {
            "name": "input",
            "coordinates": [
                [0.0, 0.0],
                [0.1, 0.2],
                [1.0, 2.0],
                [1.2, 1.9],
                [2.0, 3.0],
                [1.8, 3.3],
                [3.0, 1.0],
                [3.3, 0.7],
            ],
        },
        "target": {
            "name": "output",
            "coordinates": [
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
                [1.0, 3.0, 4.0],
                [1.0, 3.0, 4.0],
                [4.0, 5.0, 9.0],
                [4.0, 5.0, 9.0],
                [9.0, 4.0, 1.0],
                [9.0, 4.0, 1.0],
            ],
        },
    }
    (case_path / "conformance.toml").write_text(tomli_w.dumps(conformance))


def main() -> int:
    make_displacements()
    make_coordinates_1d()
    make_coordinates_2d_3d()
    return 0


if __name__ == "__main__":
    sys.exit(main())
