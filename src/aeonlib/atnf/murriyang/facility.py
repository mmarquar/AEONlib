from aeonlib.atnf.facility import AtnfFacility
from aeonlib.conf import Settings


class MurriyangFacility(AtnfFacility):
    """Client for the ATNF service that turns Murriyang requests into
    Scheduling Blocks."""

    def api_root(self, settings: Settings) -> str:
        if not settings.murriyang_api_root:
            raise ValueError("AEON_MURRIYANG_API_ROOT is not set")
        return settings.murriyang_api_root

    def api_key(self, settings: Settings) -> str:
        if not settings.murriyang_token:
            raise ValueError("AEON_MURRIYANG_TOKEN is not set")
        return settings.murriyang_token
