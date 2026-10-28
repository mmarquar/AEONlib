from aeonlib.atnf.facility import AtnfFacility
from aeonlib.conf import Settings
from aeonlib.conf import settings as default_settings


class AskapFacility(AtnfFacility):
    """Client for the ATNF service that turns ASKAP requests into Scheduling
    Blocks."""

    def __init__(self, settings: Settings = default_settings):
        if not settings.askap_api_root:
            raise ValueError("AEON_ASKAP_API_ROOT is not set")
        if not settings.askap_token:
            raise ValueError("AEON_ASKAP_TOKEN is not set")
        super().__init__(settings.askap_api_root, settings.askap_token)
