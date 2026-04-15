# ome-zarr-transformations-conformance

Test fixtures for RFC-5 transformations for OME-Zarr.

## Structure

Each directory in `./cases/` represents a test case.
It is an OME-Zarr Scene; it contains a `zarr.json` whose `attributes` contains an `ome` object which itself contains a `scene` object as described by the OME-Zarr v0.6+ specification.
This scene contains a transform graph.

### The dingus

Implementations of OME-Zarr transformations should provide a "dingus" CLI whose last 4 positional arguments MUST be:

- `PATH`: a path to an OME-Zarr hierarchy on the file system
- `SOURCE`: the name of the source coordinate system
- `TARGET`: the name of the target coordinate system
- `COORDINATES`: a JSON-serialised array of D-length arrays of numbers, where D is the dimensionality of a single coordinates

The dingus MUST then

1. open the OME-Zarr hierarchy at `PATH` and parse the `$.ome.scene` from the attributes
2. calculate a transformation from the coordinate system with name specified by `SOURCE` to the coordinate system with name specified by `TARGET` (this may require inverting one or more transforms)
3. apply this transformation to the `COORDINATES` array
4. print to STDOUT a JSON-serialised [Response](#object-response) object
5. exit with status code 0

If any of the above steps are not supported by the implementation, the dingus MUST exit with a status code other than 0.
It MAY print to STDOUT a JSON-serialised [Error](#object-response) object.

#### Object: Response

| field | necessity | type | description |
| ----- | --------- | ---- | ----------- |
| coordinates | MUST | array of array of number | The resulting coordinates from transforming the input. |

#### Object: Error

| field | necessity | type | description |
| ----- | --------- | ---- | ----------- |
| message | MAY | string | free-text description of failure |

### Test procedure

Each OME-Zarr hierarchy additionally includes a `conformance.toml`, which describes the test case.
The implementation's dingus CLI does not need to parse this.

The `transform_conformance.py` script:

- iterates through all test cases
- parses the `conformance.toml`
- calls the provided dingus CLI, supplying the test case path, the source and target coordinate system names, and the source coordinates
- reads the output of the dingus CLI
  - if the return code is 0
    - if `should_error = false`, parse the response and check the output coordinates against those defined in `target.coordinates`, using the defined tolerances
    - if `should_error = true`, fail the test
  - if the return code is non-zero
    - if `should_error = true`, pass the test
    - if `should_error = false`, fail the test
- builds a table of test successes and failures, potentially including any messages returned by the dingus CLI

It is called like:

```sh
./transformation_conformance.py ./cases -- myDingus --some-arg anotherArg
```

The dingus would then be called repeatedly, seeing arguments like

```sh
myDingus --some-arg anotherArg './cases/translation.ome.zarr' 'input' 'output' '[[1, 2]]'
```
