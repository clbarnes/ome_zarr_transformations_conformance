#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14,<4.0"
# dependencies = ["numpy>=2.0", "zarr"]
# ///
import numpy as np

N_DECIMALS = 3


def toml_print(
    arr: np.ndarray, name: str | None = None, n_decimals: int | None = N_DECIMALS
):
    if n_decimals is not None:
        arr = np.round(arr, n_decimals)
    lst = arr.tolist()
    if name:
        s = f"{name} = "
    else:
        s = ""
    s += "[\n"
    for inner in lst:
        s += "  [ "
        first = True
        for n in inner:
            if first:
                first = False
            else:
                s += ", "
            s += f"{n}"
        s += " ],\n"
    s += "]"
    print(s)


def rotation():
    theta = 1.4
    rotation = np.array(
        [
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)],
        ]
    )

    rotation = np.round(rotation, decimals=N_DECIMALS)
    toml_print(rotation, "rotation")

    coords = np.array([[-1, -1], [0, 0], [1, 1], [2, 2]])
    print("# input")
    toml_print(coords, "coordinates")

    out = rotation @ coords.T
    print("# output")
    toml_print(out.T, "coordinates")

    inv = np.linalg.inv(rotation)
    toml_print(np.round(inv, N_DECIMALS), "inv_rotation")
    inverted = inv @ out
    toml_print(inverted.T, "untransformed")


def expand(homogeneous: np.ndarray) -> np.ndarray:
    width = homogeneous.shape[-1]
    t = np.eye(width)
    t[:-1, :] = homogeneous
    return t


def unexpand(affine: np.ndarray) -> np.ndarray:
    assert np.allclose(affine[-1, :-1], 0)
    assert np.allclose(affine[-1, -1], 1)
    return affine[:-1, :]


def affine_inv(homogeneous: np.ndarray) -> np.ndarray:
    t = np.linalg.inv(expand(homogeneous))
    assert np.allclose(t[-1, :-1], 0)
    assert np.allclose(t[-1, -1], 1)
    return t[:-1, :]


def affine():
    # fmt: skip
    scale_affine = np.array(
        [
            [2, 0, 0, 0],
            [0, 3, 0, 0],
            [0, 0, 4, 0],
        ],
        float,
    )
    translation_affine = np.array(
        [
            [1, 0, 0, 10],
            [0, 1, 0, 20],
            [0, 0, 1, 30],
        ],
        float,
    )
    # applies translation then scale
    affine = unexpand(expand(scale_affine) @ expand(translation_affine))

    toml_print(affine, "affine")

    coords = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1], [2, 2, 2]], float)
    print("# input")
    toml_print(coords, "coordinates")

    out = apply_affine(affine, coords)
    print("# output")
    toml_print(out, "coordinates")

    inv = affine_inv(affine)
    toml_print(inv, "inv_affine")
    inverted = apply_affine(inv, out)
    toml_print(inverted, "untransformed")


def apply_affine(affine: np.ndarray, coords: np.ndarray) -> np.ndarray:
    lin_map = affine[:, :-1]
    translation = affine[:, -1]
    _, n_dim = coords.shape
    assert (n_dim,) == translation.shape
    out = coords @ lin_map.T
    out += translation
    return out


if __name__ == "__main__":
    # rotation()
    affine()
