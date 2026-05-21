#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "numpy>=2.4.6",
#     "zarr>=3.2.1",
# ]
# ///
import sys
from pathlib import Path
import shutil

import zarr
import numpy as np


to_do = ("affine", "affine_inverse", "rotation", "rotation_inverse")
dtypes = ("float32", "float64")

case_dir = Path(__file__).resolve().parent.parent / "cases"


def process_dtype(
    orig_path: Path, arrays: dict[str, np.ndarray], dtype: str, grp_attrs: dict
):
    path = orig_path.with_name(f"{orig_path.name.split('.')[0]}_path_{dtype}.ome.zarr")
    if path.exists():
        shutil.rmtree(path)
    shutil.copytree(orig_path, path)
    scene_grp = zarr.open_group(path)
    scene_grp.attrs.clear()
    for k, v in grp_attrs.items():
        scene_grp.attrs[k] = v
    ct_grp = scene_grp.create_group("coordinateTransformations")
    for name, arr in arrays.items():
        ct_grp.create_array(name, data=arr.astype(dtype), compressors=None)


def process_case(name: str):
    case_path = case_dir / f"{name}.ome.zarr"
    scene_grp = zarr.open_group(case_path)
    attrs = scene_grp.attrs.asdict()
    to_write = dict()
    for ct in attrs["ome"]["scene"]["coordinateTransformations"]:  # type: ignore
        tp = ct["type"]
        if tp not in ("affine", "rotation"):
            continue
        arr = np.array(ct.pop(tp), float)
        ct["path"] = "coordinateTransformations/" + ct["name"]
        to_write[ct["name"]] = arr

    for dt in dtypes:
        process_dtype(case_path, to_write, dt, attrs)


def main() -> int:
    for case in to_do:
        process_case(case)
    return 0


if __name__ == "__main__":
    sys.exit(main())
