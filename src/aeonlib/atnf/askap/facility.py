from aeonlib.atnf.facility import AtnfFacility
from aeonlib.conf import Settings


class AskapFacility(AtnfFacility):
    """Client for the ATNF service that turns ASKAP requests into Scheduling
    Blocks."""

    def api_root(self, settings: Settings) -> str:
        if not settings.askap_api_root:
            raise ValueError("AEON_ASKAP_API_ROOT is not set")
        return settings.askap_api_root

    def api_key(self, settings: Settings) -> str:
        if not settings.askap_token:
            raise ValueError("AEON_ASKAP_TOKEN is not set")
        return settings.askap_token
