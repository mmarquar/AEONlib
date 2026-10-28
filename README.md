# AEONlib

A suite of modules to enable TDA/MMA observations

[code](https://github.com/AEONplus/AEONlib)

[issues](https://github.com/AEONplus/AEONlib/issues)

# Purpose

An increasing amount of observatories and instruments related to time-domain astronomy are coming online
with programmatic abilities from the start. While most of these APIs are unique, AEONLib attempts to unify
and abstract as much as possible. Thus AEONLib can be thought of as a suite of client libraries with shared structure and code. The goal is to make writing observing programs for multiple facilities as easy and intuitive as possible.

AEONLib is not a "write once, observe everywhere" meta-language. Every observing facility provides unique
opportunities to do science and it is not the goal of AEONLib to paper over differences in order to 
achieve homogeneity. 

For concrete examples, see the iPython notebooks in the [examples/](examples/) directory. The
[tests/](tests/) are also illustrative.

# Configuration

Many of the facilities and services accessed by AEONlib require specific configuration such
as api keys, urls, etc. All configuration can be supplied by either supplying a .env file or
setting environmental variables in the execution environment.

Example .env file:

```
AEON_LCO_API_ROOT="https://observe.lco.global/api"
AEON_LCO_TOKEN="my-api-token"
```

Or set environmental variables via the shell:

```bash
export AEON_LCO_API_ROOT="https://observe.lco.global/api"
export AEON_LCO_TOKEN="my-api-token"
```

All configuration keys are prefixed with AEON_ to prevent conflicts. See the documentation for
each service to see which configuration keys are available, or check
[conf.py](src/aeonlib/conf.py)

Environmental variables take precedence over .env files. See the
[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) documentation
for more details.


# Testing

This project uses [pytest](https://docs.pytest.org/) to run tests:

```bash
pytest
```

Some tests are marked as `online`. These tests make real http requests in order
to test interfaces with various services. To run them:

```bash
pytest -m online
```

A subset of `online` tests are marked as `side_effect`. These are tests that change data on remote
systems. For example, a test might be testing creating new observation requests, or updating the
status of one. You might want to disable these:

```bash
pytest -m "not side_effect"
```

CI does not run tests marked as online.

## Viewing logs during tests

Aeonlib turns on the Pytest
[Live Logging](https://docs.pytest.org/en/stable/how-to/logging.html#live-logs) feature.
By default any logging calls with a level above `WARNING` will be displayed to the console
during the test run. It may be helpful to display debug logging, especially if debugging remote
facilities or services:

```bash
pytest -m online --log-cli-level=debug
```

# Linting

All code is formatted via [ruff](https://astral.sh/ruff).

# Code Generation

Las Cumbres Observatory [instrument classes](src/aeonlib/ocs/lco/instruments.py)
are generated via the [generator.py](codegen/lco/generator.py) script. This script
takes as input the [OCS instruments api](https://observe.lco.global/api/instruments/)
in order to produce definitions of all instruments currently available on the network.

To update the definitions, first make sure you have installed the `codegen` dependency
group:

```bash
uv sync --group codegen  # or poetry install --with codegen
```

This ensures regular users of the library do not need to install these dependencies.

The `generate.py` script takes as input JSON as produced by the instruments endpoint:

```bash
codegen/lco/generator.py {facility} instruments.json
```

Or directly from stdin using a pipe:

```bash
curl https://observe.lco.global/api/instruments/ | codegen/lco/generator.py {facility}
```

If the output looks satisfactory, you can redirect the output to overwrite the
LCO instruments definition file:

```bash
curl https://observe.lco.global/api/instruments/ | codegen/lco/generator.py {facility} > src/aeonlib/ocs/lco/instruments.py
```

# Supported Facilities

This list is a work in progress.

## Las Cumbres Observatory (LCO)

### Dependency group

Las Cumbres Observatory requires no additional dependency groups to be installed.

### Configuration Values

See [configuration](#configuration) for instructions on setting these values.

```python
lco_token: str = ""
lco_api_root: str = "https://observe.lco.global/api/"
```

### Helpful links

* [LCO Observation Portal](https://observe.lco.global/)
* [LCO Developer Documentation](https://developers.lco.global/)
* [OCS API Documentation](https://observatorycontrolsystem.github.io/api/observation_portal/)

## SOAR

SOAR is functionally the same as LCO, but has its own set of instruments and can be configured separately.

### Dependency group

SOAR requires no additional dependency groups to be installed.

### Configuration Values

See [configuration](#configuration) for instructions on setting these values.

```python
soar_token: str = ""
soar_api_root: str = "https://observe.lco.global/api/"
```

Note: the soar API token will default to the same value as lco_token, if it is set.

## BLANCO

BLANCO is functionally the same as LCO, but has its own set of instruments and can be configured separately.

### Dependency group

BLANCO requires no additional dependency groups to be installed.

### Configuration Values

See [configuration](#configuration) for instructions on setting these values.

```python
blanco_token: str = ""
blanco_api_root: str = "https://observe.lco.global/api/"
```

Note: the blanco API token will default to the same value as lco_token, if it is set.

## ESO (European Southern Observatory)

Full documentation: TODO

### Dependency Group

To use the ESO facility, you must install the `eso` group:

```bash
pip install aeonlib[eso]
uv sync --extra eso
poetry install --with eso
```

### Configuration Values

See [configuration](#configuration) for instructions on setting these values.

```python
eso_environment: str = "demo"
eso_username: str = ""
eso_password: str = ""
```

### Helpul links

* [ESO Phase 2 API](https://www.eso.org/sci/observing/phase2/p2intro/Phase2API.html)
* [ESO Phase 2 Demo Application](https://www.eso.org/p2demo/home)

## LT (Liverpool Telescope)

### Dependency Group

To use the LT facility, you must install the `lt` group:

```bash
pip install aeonlib[lt]
uv sync --extra lt
poetry install --with lt
```

### Configuration Values

See [configuration](#configuration) for instructions on setting these values.

```python
lt_username: str = ""
lt_password: str = ""
lt_host: str = ""
lt_port: str = ""
```

### Helpful links

* [LT Phase 2 Information](https://telescope.livjm.ac.uk/PropInst/Phase2/)

## SAAO (South African Astronomical Observatory)

### Configuration Values

```python
    saao_token: str = ""
saao_api_root: str = "https://ocsio.saao.ac.za/api/"
```

### Helpful links

* [SAAO Observatory Control System](https://ocsio.saao.ac.za/create)

## SALT (Southern African Large Telescope)

### Dependency Group

To use the SALT facility, you must install the `salt` group:

```bash
pip install aeonlib[salt]
uv sync --extra salt
poetry install --with salt
```

### Configuration values

See [configuration](#configuration) for instructions on setting these values.

```python
salt_username: str = ""
salt_password = ""
```

The username and password are those you would use for the [SALT Web Manager](https://www.salt.ac.za/wm/).

## Gemini

### Dependency Group

The use the Gemini facility, you must install the `gemini` group:

```bash
pip install aeonlib[gemini]
uv sync --extra gemini
poetry install --with gemini
```

### Configuration Values
```python
  gemini_token: str = ""
  gemini_environment: Literal["production", "development"] = "production"
  gemini_debug: bool = False
```

The GPP client selects an environment automatically depending on which package version is
installed. We override that here so the environment can be configured, otherwise it would
be necessary to install a different package to test/deploy.

### Helpful Links

[gpp-client documentation](https://gpp-client.readthedocs.io/en/latest/client.html)

### GPP Client direct access
This module installs gpp-client, which is already a fully-features client for gemini. Thus
AEONLib acts as a thin wrapper with some convenience functions. The gpp client can be
accessed directly via facility.client

## Canada France Hawaii Telescope (CFHT)

### Configuration values

```python
cfht_api_root: str = "https://api-stage.cfht.hawaii.edu/"
cfht_access_token: str = ""
```

### Helpful Links

[Kealahou Phase 1 & 2 tool - staging](https://hou-stage.cfht.hawaii.edu/)

## Murriyang (Parkes radio telescope)

Murriyang is operated by CSIRO's Australia Telescope National Facility (ATNF).
The observatory cannot be called from outside, so requests are queued on a
relay that both sides can reach. The observatory polls the relay and turns each
request into a Scheduling Block, so `submit_observation` returns a ticket at once
and you poll for progress. Only tracking a single sidereal (ICRS) target is supported, with the UWL
receiver (`UwlTrack`) or the CryoPAF receiver (`CryopafTrack`). Each class offers
only the settings that apply to its receiver.

### Configuration values

See [configuration](#configuration) for instructions on setting these values.

```python
murriyang_api_root: str = ""
murriyang_token: str = ""
```

### Usage

`target` and `duration` (seconds) are required. Every other field overrides the
observatory's defaults for that receiver, so leave it unset unless you need it.

```python
from aeonlib.atnf.murriyang.facility import MurriyangFacility
from aeonlib.atnf.murriyang.models import CryopafTrack
from aeonlib.models import SiderealTarget

track = CryopafTrack(
    target=SiderealTarget(name="S9", type="ICRS", ra="17h52m05.5s", dec="-34d25m41.8s"),
    duration=300,
)
facility = MurriyangFacility()
facility.validate_observation(track)  # local check only, no network call
ticket = facility.submit_observation(track)  # queued; returns at once
status = facility.get_observation_status(ticket)  # status.state, status.sb_id
facility.cancel_observation(ticket)  # works until the observatory picks it up
```

For a dry run, `submit_observation(track, dry_run=True)` makes the observatory
build the parset without submitting it; read it from `status.parset` once
`status.terminal` is true. Pass a timezone-aware `expires=` to stop a request
being acted on if it waits too long, which matters for a target of opportunity.

```python
status = facility.get_observation_status(ticket)
while not status.terminal:  # a real client would sleep between polls
    status = facility.get_observation_status(ticket)
```

### Generated models

`src/aeonlib/atnf/_generated.py` (shared by Murriyang and ASKAP) is generated from
ATNF's Scheduling Block parameter definitions, so do not edit it.
`just update-atnf` regenerates it and needs the ATNF-provided
`atnf-aeonlib-bridge` package.

## ASKAP

Like Murriyang, requests are queued on a relay for the observatory to pick up
(see above for `get_observation_status`, `cancel_observation`, `dry_run` and
`expires`). `AskapStandard` observes one sidereal (ICRS) target, for
example a target of opportunity.

### Configuration values

See [configuration](#configuration) for instructions on setting these values.

```python
askap_api_root: str = ""
askap_token: str = ""
```

### Usage

`target` and `duration` (seconds) are required. Every other field overrides the
observatory's default, so leave it unset unless you need it.

```python
from aeonlib.atnf.askap.facility import AskapFacility
from aeonlib.atnf.askap.models import AskapStandard
from aeonlib.models import SiderealTarget

request = AskapStandard(
    target=SiderealTarget(name="GRB261010A", type="ICRS", ra=248.749083, dec=26.580194),
    duration=21600,
)
facility = AskapFacility()
ticket = facility.submit_observation(request, dry_run=True)  # nothing is submitted
```
