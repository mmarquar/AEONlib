from typing import Annotated, ClassVar

from pydantic import Field

from aeonlib.atnf import _generated
from aeonlib.atnf.models import TargetRequest


class UwlTrack(_generated.UwlTrack, TargetRequest):
    """Track one sidereal target with the Murriyang UWL receiver.

    Only ``target`` and ``duration`` normally need setting. Every other field
    overrides the observatory's default; leave it unset to keep that.
    """

    mode: ClassVar[str] = "track"


class CryopafTrack(_generated.CryopafTrack, TargetRequest):
    """Track one sidereal target with the Murriyang CryoPAF receiver.

    Only ``target`` and ``duration`` normally need setting. Every other field
    overrides the observatory's default; leave it unset to keep that.
    """

    mode: ClassVar[str] = "track"


MURRIYANG_TRACKS = Annotated[UwlTrack | CryopafTrack, Field(discriminator="receiver")]
"""Any Murriyang track request. The ``receiver`` value picks the class, so a
server can parse a request body with ``TypeAdapter(MURRIYANG_TRACKS)``."""
