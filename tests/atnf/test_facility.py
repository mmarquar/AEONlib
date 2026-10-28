import json
from datetime import UTC, datetime

import httpx
import pytest

from aeonlib.atnf.facility import TERMINAL_STATES, AtnfNetworkError
from aeonlib.atnf.murriyang.facility import MurriyangFacility
from aeonlib.atnf.murriyang.models import CryopafTrack, UwlTrack
from aeonlib.conf import Settings
from aeonlib.exceptions import AuthenticationError
from aeonlib.models import SiderealTarget

API_ROOT = "http://relay.test/api"


@pytest.fixture
def track():
    target = SiderealTarget(name="S9", type="ICRS", ra=268.0, dec=-34.4)
    return CryopafTrack(target=target, duration=300)


def _facility(handler):
    facility = MurriyangFacility(
        Settings(murriyang_api_root=API_ROOT, murriyang_token="secret")
    )
    facility._client = httpx.Client(
        base_url=API_ROOT + "/",
        headers={"Authorization": "Bearer secret"},
        transport=httpx.MockTransport(handler),
    )
    return facility


def test_settings_are_required():
    with pytest.raises(ValueError, match="AEON_MURRIYANG_API_ROOT"):
        MurriyangFacility(Settings(murriyang_api_root="", murriyang_token="t"))
    with pytest.raises(ValueError, match="AEON_MURRIYANG_TOKEN"):
        MurriyangFacility(Settings(murriyang_api_root=API_ROOT, murriyang_token=""))


def test_submit_queues_the_request_and_returns_a_ticket(track):
    seen = {}

    def handler(request):
        seen["method"], seen["url"] = request.method, str(request.url)
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(202, json={"id": "abc123"})

    ticket = _facility(handler).submit_observation(track)

    assert ticket == "abc123"
    assert (seen["method"], seen["url"]) == ("POST", "http://relay.test/api/requests")
    assert seen["auth"] == "Bearer secret"
    assert seen["body"]["mode"] == "track"
    assert seen["body"]["dry_run"] is False
    assert "expires" not in seen["body"]
    assert seen["body"]["request"]["receiver"] == "cryopaf"
    assert seen["body"]["request"]["target"]["name"] == "S9"


def test_dry_run_and_expiry_are_sent(track):
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        return httpx.Response(202, json={"id": 7})

    expires = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
    ticket = _facility(handler).submit_observation(track, dry_run=True, expires=expires)

    assert ticket == "7"
    assert seen["body"]["dry_run"] is True
    assert seen["body"]["expires"] == "2026-10-20T12:00:00+00:00"


def test_expiry_must_be_timezone_aware(track):
    def handler(request):
        raise AssertionError("no request expected")

    with pytest.raises(ValueError, match="timezone aware"):
        _facility(handler).submit_observation(track, expires=datetime(2026, 10, 20))  # noqa: DTZ001


def test_status_reports_progress_and_results():
    def handler(request):
        assert request.method == "GET"
        assert str(request.url) == "http://relay.test/api/requests/abc123"
        return httpx.Response(
            200, json={"state": "VALIDATED", "parset": "x = 1\n", "extra": "ignored"}
        )

    status = _facility(handler).get_observation_status("abc123")

    assert status.state == "VALIDATED"
    assert status.parset == "x = 1\n"
    assert status.sb_id is None
    assert status.terminal


def test_a_pending_request_is_not_terminal():
    facility = _facility(lambda request: httpx.Response(200, json={"state": "PENDING"}))

    assert not facility.get_observation_status("abc123").terminal
    assert "PENDING" not in TERMINAL_STATES


def test_cancel_returns_whether_it_worked():
    assert _facility(lambda request: httpx.Response(204)).cancel_observation("a")
    assert not _facility(lambda request: httpx.Response(409)).cancel_observation("a")


def test_validate_observation_is_local_and_returns_the_sb_params(track):
    def handler(request):
        raise AssertionError("no request expected")

    params = _facility(handler).validate_observation(track)

    assert params["duration"] == 300.0
    assert params["field_name"] == "S9"


@pytest.mark.parametrize("status", [401, 403])
def test_rejected_token_is_an_authentication_error(track, status):
    facility = _facility(lambda request: httpx.Response(status))

    with pytest.raises(AuthenticationError):
        facility.submit_observation(track)


def test_relay_error_is_a_network_error(track):
    facility = _facility(lambda request: httpx.Response(500))

    with pytest.raises(AtnfNetworkError, match="500"):
        facility.submit_observation(track)


def test_unknown_ticket_is_a_network_error():
    facility = _facility(lambda request: httpx.Response(404))

    with pytest.raises(AtnfNetworkError, match="404"):
        facility.get_observation_status("nope")


def test_unreachable_relay_is_a_network_error(track):
    def handler(request):
        raise httpx.ConnectError("down")

    with pytest.raises(AtnfNetworkError, match="Could not reach"):
        _facility(handler).submit_observation(track)


def test_response_without_a_ticket_is_a_network_error(track):
    facility = _facility(lambda request: httpx.Response(202, json={"other": 1}))

    with pytest.raises(AtnfNetworkError, match="Unusable response"):
        facility.submit_observation(track)


def test_unsupported_target_fails_before_any_request():
    target = SiderealTarget(name="x", type="HOUR_ANGLE", ra=1.0, dec=1.0)
    track = UwlTrack(target=target, duration=300)

    def handler(request):
        raise AssertionError("no request expected")

    facility = _facility(handler)
    with pytest.raises(ValueError, match="only supports ICRS"):
        facility.submit_observation(track)
    with pytest.raises(ValueError, match="only supports ICRS"):
        facility.validate_observation(track)
