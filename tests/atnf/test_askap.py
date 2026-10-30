import json

import httpx
import pytest

from aeonlib.atnf.askap.facility import AskapFacility
from aeonlib.atnf.askap.models import AskapStandard
from aeonlib.conf import Settings
from aeonlib.models import SiderealTarget

API_ROOT = "http://askap-relay.test/api"


@pytest.fixture
def target():
    return SiderealTarget(name="GRB261010A", type="ICRS", ra=248.749083, dec=26.580194)


def test_minimal_request_sets_only_the_caller_fields(target):
    request = AskapStandard(target=target, duration=21600)

    assert request.to_sb_params() == {
        "duration": 21600.0,
        "field_name": "GRB261010A",
        "field_direction": [248.749083, 26.580194, "J2000"],
    }


def test_a_setting_opl_does_not_model_can_still_be_tuned(target):
    request = AskapStandard(target=target, duration=21600, align_to_beam=0)

    assert request.to_sb_params()["align_to_beam"] == 0


def test_offers_only_askap_settings():
    fields = AskapStandard.model_fields

    assert "receiver" not in fields
    assert "corrmode" in fields
    assert "footprint" in fields
    assert "stream" not in fields
    assert "sun_override" not in fields  # deliberately not offered


def test_settings_are_required():
    with pytest.raises(ValueError, match="AEON_ASKAP_API_ROOT"):
        AskapFacility(Settings(askap_api_root="", askap_token="t"))
    with pytest.raises(ValueError, match="AEON_ASKAP_TOKEN"):
        AskapFacility(Settings(askap_api_root=API_ROOT, askap_token=""))


def test_submit_queues_a_standard_request(target):
    sent = []

    def handler(request):
        sent.append(request)
        return httpx.Response(201)

    facility = AskapFacility(
        Settings(askap_api_root=API_ROOT, askap_token="t"),
        transport=httpx.MockTransport(handler),
    )
    request_id = facility.submit_observation(
        AskapStandard(target=target, duration=60), dry_run=True
    )

    assert sent[0].url == f"{API_ROOT}/requests/{request_id}"
    body = json.loads(sent[0].content)
    assert body["mode"] == "standard"
    assert body["dry_run"] is True
    assert "receiver" not in body["request"]
