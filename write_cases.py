#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["tomli_w", "tomli>=2.4"]
# ///
import tomli
import tomli_w
import json
import shutil
from pathlib import Path

here = Path(__file__).resolve().parent
configs = here / "cases_config"
cases = here / "cases"


def main():
    for config_path in here.joinpath("cases_config").glob("*.toml"):
        d = tomli.loads(config_path.read_text())
        conformance = d["conformance"]
        oz_name = config_path.stem + ".ome.zarr"
        oz_path = cases / oz_name
        if oz_path.exists():
            shutil.rmtree(oz_path)
        oz_path.mkdir()
        zarr_json = {
            "zarr_format": 3,
            "node_type": "group",
            "attributes": {"ome": {"version": "0.6", "scene": {**d["scene"]}}},
        }
        oz_path.joinpath("zarr.json").write_text(json.dumps(zarr_json, indent=2))
        oz_path.joinpath("conformance.toml").write_text(tomli_w.dumps(conformance))

        if not d.get("invert"):
            return

        oz_name = config_path.stem + "_inverse.ome.zarr"
        oz_path = cases / oz_name
        if oz_path.exists():
            shutil.rmtree(oz_path)
        oz_path.mkdir()
        oz_path.joinpath("zarr.json").write_text(json.dumps(zarr_json, indent=2))
        conformance["source"], conformance["target"] = (
            conformance["target"],
            conformance["source"],
        )
        oz_path.joinpath("conformance.toml").write_text(tomli_w.dumps(conformance))


if __name__ == "__main__":
    main()
