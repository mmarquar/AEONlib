import json
from datetime import UTC, datetime

import httpx
import pytest

from aeonlib.atnf.facility import AtnfNetworkError
from aeonlib.atnf.murriyang.facility import MurriyangFacility
from aeonlib.atnf.murriyang.models import CryopafTrack, UwlTrack
from aeonlib.conf import Settings
from aeonlib.exceptions import AuthenticationError
from aeonlib.models import SiderealTarget

SETTINGS = Settings(
    murriyang_api_root="https://relay.test/api", murriyang_token="secret"
)


@pytest.fixture
def track():
    target = SiderealTarget(name="S9", type="ICRS", ra=268.0, dec=-34.4)
    return CryopafTrack(target=target, duration=300)


def facility(handler) -> MurriyangFacility:
    return MurriyangFacility(SETTINGS, transport=httpx.MockTransport(handler))


def test_settings_are_required():
    with pytest.raises(ValueError, match="AEON_MURRIYANG_API_ROOT"):
        MurriyangFacility(Settings(murriyang_api_root="", murriyang_token="t"))
    with pytest.raises(ValueError, match="AEON_MURRIYANG_TOKEN"):
        MurriyangFacility(
            Settings(murriyang_api_root="https://relay.test", murriyang_token="")
        )


def test_submit_puts_the_request_under_its_id(track):
    sent = []

    def handler(request):
        sent.append(request)
        return httpx.Response(201)

    request_id = facility(handler).submit_observation(track)

    assert sent[0].method == "PUT"
    assert sent[0].url == f"https://relay.test/api/requests/{request_id}"
    assert sent[0].headers["Authorization"] == "Bearer secret"
    body = json.loads(sent[0].content)
    assert body["mode"] == "track"
    assert body["token"] == "secret"
    assert body["dry_run"] is False
    assert "expires" not in body
    assert body["request"]["receiver"] == "cryopaf"
    assert body["request"]["target"]["name"] == "S9"


def test_submit_uses_the_given_id_and_options(track):
    sent = []

    def handler(request):
        sent.append(request)
        return httpx.Response(200)

    expires = datetime(2026, 11, 1, tzinfo=UTC)
    request_id = facility(handler).submit_observation(
        track, request_id="r1", dry_run=True, expires=expires
    )

    assert request_id == "r1"
    assert sent[0].url.path == "/api/requests/r1"
    body = json.loads(sent[0].content)
    assert body["dry_run"] is True
    assert body["expires"] == "2026-11-01T00:00:00+00:00"


def test_naive_expiry_is_rejected(track):
    with pytest.raises(ValueError, match="timezone"):
        facility(lambda request: httpx.Response(201)).submit_observation(
            track, expires=datetime.fromisoformat("2026-11-01")
        )


def test_unsupported_target_is_rejected_locally():
    target = SiderealTarget(name="x", type="HOUR_ANGLE", ra=1.0, dec=1.0)
    track = UwlTrack(target=target, duration=300)
    unused = facility(lambda request: httpx.Response(500))

    with pytest.raises(ValueError, match="only supports ICRS"):
        unused.validate_observation(track)
    with pytest.raises(ValueError, match="only supports ICRS"):
        unused.submit_observation(track)


def test_validate_observation_returns_the_sb_params(track):
    params = facility(lambda request: httpx.Response(500)).validate_observation(track)

    assert params["duration"] == 300.0
    assert params["field_name"] == "S9"


@pytest.mark.parametrize(
    ("state", "terminal"), [("PENDING", False), ("VALIDATED", True)]
)
def test_status(state, terminal):
    status = facility(
        lambda request: httpx.Response(200, json={"state": state, "parset": "x = 1\n"})
    ).get_observation_status("r1")

    assert status.state == state
    assert status.terminal is terminal
    assert status.parset == "x = 1\n"
    assert status.sb_id is None


def test_unusable_status_is_a_network_error():
    with pytest.raises(AtnfNetworkError):
        facility(lambda request: httpx.Response(200, json={})).get_observation_status(
            "r1"
        )


@pytest.mark.parametrize(("code", "cancelled"), [(204, True), (409, False)])
def test_cancel(code, cancelled):
    assert (
        facility(lambda request: httpx.Response(code)).cancel_observation("r1")
        is cancelled
    )


@pytest.mark.parametrize("code", [401, 403])
def test_rejected_token(code, track):
    with pytest.raises(AuthenticationError):
        facility(lambda request: httpx.Response(code)).submit_observation(track)


@pytest.mark.parametrize("code", [404, 409, 500])
def test_relay_error(code, track):
    with pytest.raises(AtnfNetworkError, match=str(code)):
        facility(lambda request: httpx.Response(code)).submit_observation(track)


def test_unreachable_relay(track):
    def handler(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(AtnfNetworkError, match="reach"):
        facility(handler).submit_observation(track)
