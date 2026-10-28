from typing import ClassVar

from aeonlib.atnf import _generated
from aeonlib.atnf.models import TargetRequest


class AskapStandard(_generated.AskapStandard, TargetRequest):
    """Observe one sidereal target with ASKAP, for example a target of
    opportunity.

    Only ``target`` and ``duration`` normally need setting. Every other field
    overrides the observatory's default; leave it unset to keep that.
    """

    mode: ClassVar[str] = "standard"
