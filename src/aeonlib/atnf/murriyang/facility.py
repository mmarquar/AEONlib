from aeonlib.atnf.facility import AtnfFacility
from aeonlib.conf import Settings
from aeonlib.conf import settings as default_settings


class MurriyangFacility(AtnfFacility):
    """Client for the ATNF service that turns Murriyang requests into
    Scheduling Blocks."""

    def __init__(self, settings: Settings = default_settings):
        if not settings.murriyang_api_root:
            raise ValueError("AEON_MURRIYANG_API_ROOT is not set")
        if not settings.murriyang_token:
            raise ValueError("AEON_MURRIYANG_TOKEN is not set")
        super().__init__(settings.murriyang_api_root, settings.murriyang_token)
