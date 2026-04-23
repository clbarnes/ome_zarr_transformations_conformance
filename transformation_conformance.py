#!/usr/bin/env python3
"""
May be called as a standalone python script,
or as `oztc` if pip-installed.

Test with

```sh
./transformation_conformance.py cases -- sh -c 'echo "{\"coordinates\": [[1,2],[3,4],[5,6]]}"'
```
"""

from __future__ import annotations
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
import os
import subprocess as sp
from argparse import ArgumentParser
from pathlib import Path
import sys
import re
import json
from dataclasses import dataclass
from typing import Any, Iterable, Literal, Self
import logging
import tomllib
import importlib.resources


logger = logging.getLogger("ome_zarr_conformance")


@dataclass
class Response:
    coordinates: list[list[float]]
    message: str | None = None

    @classmethod
    def from_jso(cls, jso: dict[str, Any]) -> Self:
        return cls(**jso)


@dataclass
class Error:
    message: str | None = None

    @classmethod
    def from_jso(cls, jso: dict[str, Any]) -> Self:
        return cls(**jso)


@dataclass
class TestResult:
    test_name: str
    status: Literal["pass", "fail", "error"]
    message: str | None
    stderr: str
    return_code: int
    conformance: Conformance | None = None


class Requested:
    def __init__(
        self,
        exclude_patterns: list[re.Pattern] | None = None,
        include_patterns: list[re.Pattern] | None = None,
    ) -> None:
        self.exclude_patterns = exclude_patterns or []
        self.include_patterns = include_patterns or []

    def include(self, name: str) -> bool:
        if self.exclude_patterns and any(p.search(name) for p in self.exclude_patterns):
            return False
        if self.include_patterns and not any(
            p.search(name) for p in self.include_patterns
        ):
            return False
        return True


def test_path_to_name(fpath: Path, root: Path) -> str:
    w_suff = str(fpath.relative_to(root)).replace(os.path.sep, "/")
    return w_suff.split(".", 1)[0]


@dataclass
class Source:
    name: str
    coordinates: list[list[float]]

    @classmethod
    def from_jso(cls, jso: dict[str, Any]) -> Self:
        return cls(**jso)


@dataclass
class Target:
    name: str
    coordinates: list[list[float]] | None = None

    @classmethod
    def from_jso(cls, jso: dict[str, Any]) -> Self:
        return cls(**jso)


@dataclass
class Conformance:
    description: str
    should_error: bool
    absolute_tolerance: float
    relative_tolerance: float
    source: Source
    target: Target

    @classmethod
    def from_jso(cls, jso: dict[str, Any]) -> Self:
        jso["source"] = Source.from_jso(jso["source"])
        jso["target"] = Target.from_jso(jso["target"])
        return cls(**jso)


def run_test(dingus_cmd: list[str], path: Path, test_name: str) -> TestResult:
    test_logger = logger.getChild(test_name)
    d = tomllib.loads(path.joinpath("conformance.toml").read_text())
    conformance = Conformance.from_jso(d)

    coords_json = json.dumps(conformance.source.coordinates, separators=(",", ":"))
    args = [
        os.fspath(path),
        conformance.source.name,
        conformance.target.name,
        coords_json,
    ]

    command = dingus_cmd + args
    test_logger.debug("Running command %s", command)
    res = sp.run(
        dingus_cmd + args,
        text=True,
        capture_output=True,
    )
    stdout = res.stdout.strip()
    msg = None

    if res.returncode:
        if stdout:
            e = Error.from_jso(json.loads(stdout))
            msg = e.message
        if conformance.should_error:
            status = "pass"
        else:
            status = "error"
        return TestResult(
            test_name, status, msg, res.stderr, res.returncode, conformance
        )
    else:
        if stdout:
            e = Response.from_jso(json.loads(stdout))
            msg = e.message
        if conformance.should_error:
            status = "fail"
        elif conformance.target.coordinates is None:
            status = "pass"
        else:
            is_correct = check_results(
                e.coordinates,
                conformance.target.coordinates,
                conformance.absolute_tolerance,
                conformance.relative_tolerance,
            )

            if is_correct:
                status = "pass"
            else:
                status = "fail"

        return TestResult(
            test_name, status, msg, res.stderr, res.returncode, conformance
        )


def check_results(
    expected: list[list[float]], actual: list[list[float]], atol: float, rtol: float
):
    if len(expected) != len(actual):
        return False
    for exp, act in zip(expected, actual):
        if len(exp) != len(act):
            return False
        for e, a in zip(exp, act):
            diff = abs(e - a)
            if diff > atol:
                return False
            larger = max(abs(e), abs(a))
            rel = rtol * larger
            if diff > rel:
                return False
    return True


def run_all_tests(
    cmd: list[str],
    cases: dict[str, Path],
    threads=None,
) -> Iterable[TestResult]:
    with ThreadPoolExecutor(threads) as pool:
        logger.info(
            "Running %s tests with max %s threads", len(cases), pool._max_workers
        )
        futs: list[Future] = []
        for name, path in cases.items():
            futs.append(pool.submit(run_test, cmd, path, name))

        for f in futs:
            res = f.result()
            if res is not None:
                yield res


@contextmanager
def maybe_builtins(no_builtin):
    if no_builtin:
        yield None
    else:
        with importlib.resources.path(
            "transformation_conformance", "cases"
        ) as cases_path:
            yield cases_path


def collect_all_tests(case_dirs: Iterable[Path], req: Requested) -> dict[str, Path]:
    test_paths = []
    for p in case_dirs:
        for inner in p.iterdir():
            if inner.is_dir():
                test_paths.append((test_path_to_name(inner, p), inner))
    return dict(sorted((n, p) for n, p in test_paths if req.include(n)))


def main(raw_args=None):
    parser = ArgumentParser(
        description=(
            "Feed sample Zarr data into a dingus CLI for validation. "
            "After the arguments shown, add a -- followed by the dingus CLI call; "
            "e.g., `./transformation_conformance.py ./cases -- path/to/my/dingus -cli +args`. "
            "The path to the attributes file or root of the zarr container will be appended to the dingus call."
        )
    )
    parser.add_argument(
        "cases",
        type=Path,
        nargs="*",
        help=("path to directories containing test cases"),
    )
    parser.add_argument(
        "--no-builtin",
        "-B",
        action="store_true",
        help="exclude the built-in test cases",
    )
    parser.add_argument(
        "--no-exit-code",
        "-X",
        action="store_true",
        help="return exit code 0 (success) even if tests failed",
    )
    parser.add_argument(
        "--include-pattern",
        "-p",
        type=re.compile,
        action="append",
        help="regular expression pattern for test names to include; can be given multiple times (default include all)",
    )
    parser.add_argument(
        "--exclude-pattern",
        "-P",
        type=re.compile,
        action="append",
        help="regular expression pattern for test names to exclude; can be given multiple times (default exclude none)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="increase logging verbosity; can be repeated",
    )

    if raw_args is None:
        raw_args = sys.argv

    try:
        split = raw_args.index("--")
        dingus_args = raw_args[split + 1 :]
        these_args = raw_args[1:split]
    except ValueError:
        these_args = raw_args
        dingus_args = None

    args = parser.parse_args(these_args)

    lvl = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }.get(args.verbose, logging.DEBUG)
    logging.basicConfig(level=lvl)
    logging.debug("Got args: %s", args)

    if dingus_args is None:
        print(
            "No dingus command provided; add -- followed by the command",
            file=sys.stderr,
        )
        sys.exit(0)

    passes = 0
    failures = 0
    errors = 0

    req = Requested(
        exclude_patterns=args.exclude_pattern,
        include_patterns=args.include_pattern,
    )

    case_dirs = []

    with maybe_builtins(args.no_builtin) as builtin_cases:
        if builtin_cases is not None:
            case_dirs.append(builtin_cases)

        case_dirs.extend(args.cases)
        cases = collect_all_tests(case_dirs, req)

        for res in run_all_tests(
            dingus_args,
            cases,
        ):
            row = [
                res.test_name,
                res.status,
            ]
            if res.status == "pass":
                passes += 1
            elif res.status == "fail":
                failures += 1
            elif res.status == "error":
                errors += 1

            print("\t".join(row))

    logger.info("Got %s passes, %s failures, %s errors", passes, failures, errors)

    if args.no_exit_code:
        sys.exit(0)

    code = 0
    if failures:
        code += 1
    if errors:
        code += 2
    sys.exit(code)


if __name__ == "__main__":
    main()
