from astropy import units as u

from aeonlib.models import SiderealTarget


def field_direction_from_aeon(target: SiderealTarget) -> list[float | str]:
    """Convert an Aeonlib ICRS target to an ATNF ``[ra, dec, frame]`` direction.

    ATNF treats a pair of floats as decimal degrees, so the coordinates keep
    full precision and need no formatting.
    """
    if target.type != "ICRS":
        raise ValueError(
            "ATNF target conversion only supports ICRS SiderealTarget objects"
        )
    if target.proper_motion_ra or target.proper_motion_dec:
        raise ValueError(
            "ATNF directions carry no proper motion, apply it to the coordinates first"
        )

    ra = float(target.ra.to_value(u.deg)) % 360
    dec = float(target.dec.to_value(u.deg))
    return [ra, dec, "J2000"]
