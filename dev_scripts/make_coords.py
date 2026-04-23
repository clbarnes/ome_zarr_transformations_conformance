#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14,<4.0"
# dependencies = ["numpy>=2.0"]
# ///
import numpy as np

N_DECIMALS = 3


def toml_print(arr: np.ndarray, name: str | None = None):
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


def affine_transform(homogeneous: np.ndarray, coords: np.ndarray) -> np.ndarray:
    transposed = coords.T
    transposed = np.ones((coords.shape[-1] + 1, coords.shape[0]))
    transposed[:-1, :] = coords.T
    res = expand(homogeneous) @ transposed

    return res.T


def affine_inv(homogeneous: np.ndarray) -> np.ndarray:
    t = np.linalg.inv(expand(homogeneous))
    return t[:-1, :]


def affine():
    affine = np.array([[1, 0, 0, 0], [0, 1, 2, 3], [0, 4, 5, 6]])

    toml_print(affine, "affine")

    coords = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1], [2, 2, 2]])
    print("# input")
    toml_print(coords, "coordinates")

    out = affine_transform(affine, coords)
    print("# output")
    toml_print(out.T, "coordinates")

    inv = affine_inv(affine)
    toml_print(np.round(inv, N_DECIMALS), "inv_affine")
    inverted = inv @ out
    toml_print(inverted.T, "untransformed")


if __name__ == "__main__":
    # rotation()
    affine()
