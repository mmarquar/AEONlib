import pytest
from pydantic import TypeAdapter, ValidationError

from aeonlib.atnf.murriyang.facility import MurriyangFacility
from aeonlib.atnf.murriyang.models import MURRIYANG_TRACKS, CryopafTrack, UwlTrack
from aeonlib.conf import Settings
from aeonlib.models import SiderealTarget


@pytest.fixture
def target():
    return SiderealTarget(name="S9", type="ICRS", ra=268.0, dec=-34.4)


def test_minimal_request_sets_only_the_caller_fields(target):
    track = UwlTrack(program="P747", target=target, duration=300)

    assert track.receiver == "uwl"
    assert track.to_sb_params() == {
        "duration": 300.0,
        "field_name": "S9",
        "field_direction": [268.0, -34.4, "J2000"],
    }


def test_program_is_required_and_not_an_sb_parameter(target):
    with pytest.raises(ValidationError, match="program"):
        UwlTrack.model_validate({"target": target, "duration": 300})

    assert (
        "program"
        not in UwlTrack(program="P747", target=target, duration=300).to_sb_params()
    )


def test_each_receiver_offers_only_its_own_overrides():
    for name in ("footprint", "stream", "pol_axis", "filter_band"):
        assert name not in UwlTrack.model_fields
        assert name in CryopafTrack.model_fields


def test_overrides_are_included(target):
    track = CryopafTrack(
        program="P747",
        target=target,
        duration=300,
        sky_frequency=1420.4,
        cal_signal=True,
        footprint={"name": "hextile72", "pitch": 0.162},
    )

    params = track.to_sb_params()

    assert params["sky_frequency"] == 1420.4
    assert params["cal_signal"] is True
    assert params["footprint"] == {"name": "hextile72", "pitch": 0.162}
    assert "receiver" not in params
    assert "target" not in params


def test_footprint_override_must_be_complete(target):
    with pytest.raises(ValidationError, match="pitch"):
        CryopafTrack.model_validate(
            {
                "program": "P747",
                "target": target,
                "duration": 300,
                "footprint": {"name": "hextile72"},
            }
        )


def test_duration_is_required_and_bounded(target):
    with pytest.raises(ValidationError, match="duration"):
        UwlTrack.model_validate({"program": "P747", "target": target})
    with pytest.raises(ValidationError, match="duration"):
        UwlTrack.model_validate({"program": "P747", "target": target, "duration": 5})


def test_receiver_is_fixed_by_the_class(target):
    with pytest.raises(ValidationError, match="receiver"):
        UwlTrack.model_validate(
            {
                "program": "P747",
                "target": target,
                "duration": 300,
                "receiver": "cryopaf",
            }
        )


def test_json_round_trip_picks_the_class_from_the_receiver(target):
    adapter = TypeAdapter(MURRIYANG_TRACKS)
    track = CryopafTrack(
        program="P747", target=target, duration=300, pol_axis=("pa_fixed", 0.0)
    )

    parsed = adapter.validate_python(track.model_dump(mode="json", exclude_none=True))

    assert isinstance(parsed, CryopafTrack)
    assert parsed.to_sb_params() == track.to_sb_params()

    uwl = UwlTrack(program="P747", target=target, duration=60)
    assert isinstance(adapter.validate_python(uwl.model_dump(mode="json")), UwlTrack)


def test_settings_are_required():
    with pytest.raises(ValueError, match="AEON_MURRIYANG_API_ROOT"):
        MurriyangFacility(Settings(murriyang_api_root="", murriyang_token="t"))
    with pytest.raises(ValueError, match="AEON_MURRIYANG_TOKEN"):
        MurriyangFacility(
            Settings(murriyang_api_root="https://relay.test", murriyang_token="")
        )
