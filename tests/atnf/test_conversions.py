import pytest

from aeonlib.atnf.conversions import field_direction_from_aeon
from aeonlib.models import SiderealTarget


def _target(**kwargs):
    return SiderealTarget(name="test", type="ICRS", **kwargs)


def test_field_direction_from_aeon():
    result = field_direction_from_aeon(_target(ra=12.3, dec=45.6))

    assert result == [12.3, 45.6, "J2000"]


def test_field_direction_from_sexagesimal_input():
    result = field_direction_from_aeon(_target(ra="17h52m05.5s", dec="-34d25m41.8s"))

    assert result[0] == pytest.approx(268.0229166666666)
    assert result[1] == pytest.approx(-34.42827777777777)
    assert result[2] == "J2000"


def test_field_direction_coordinates_are_plain_floats():
    ra, dec, _ = field_direction_from_aeon(_target(ra=268, dec=-34))

    assert type(ra) is float
    assert type(dec) is float


def test_field_direction_wraps_negative_right_ascension():
    result = field_direction_from_aeon(_target(ra=-15.0, dec=0.0))

    assert result[0] == 345.0


def test_field_direction_rejects_non_icrs():
    target = SiderealTarget(name="test", type="HOUR_ANGLE", ra=12.3, dec=-45.6)

    with pytest.raises(ValueError, match="only supports ICRS"):
        field_direction_from_aeon(target)


def test_field_direction_rejects_proper_motion():
    target = _target(ra=12.3, dec=-45.6, proper_motion_ra=5.0)

    with pytest.raises(ValueError, match="no proper motion"):
        field_direction_from_aeon(target)
