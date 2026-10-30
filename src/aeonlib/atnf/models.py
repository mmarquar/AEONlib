from typing import Any, ClassVar

from pydantic import BaseModel, Field

from aeonlib.atnf.conversions import field_direction_from_aeon
from aeonlib.models import SiderealTarget


class TargetRequest(BaseModel):
    """Adds the observing program and sidereal target to a generated ATNF
    request model.

    ``mode`` names the observing mode; it is the path the request is sent to.
    """

    mode: ClassVar[str]
    program: str = Field(min_length=1)
    """The ATNF observing program the time is charged to."""
    target: SiderealTarget

    def to_sb_params(self) -> dict[str, Any]:
        """Return the Scheduling Block parameters this request sets.

        Fields left unset are omitted, so the observatory's defaults apply.
        """
        params = self.model_dump(
            exclude={"program", "target", "receiver"}, exclude_none=True
        )
        params["field_name"] = self.target.name
        params["field_direction"] = field_direction_from_aeon(self.target)
        return params
