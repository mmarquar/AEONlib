import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel

from aeonlib.atnf.models import TargetRequest
from aeonlib.conf import Settings
from aeonlib.conf import settings as default_settings
from aeonlib.exceptions import AuthenticationError, ServiceNetworkError

TERMINAL_STATES = frozenset({"VALIDATED", "OBSERVED", "FAILED", "CANCELLED", "EXPIRED"})


class AtnfNetworkError(ServiceNetworkError):
    pass


class ObservationStatus(BaseModel):
    state: str
    """PENDING until the observatory picks the request up, then one of
    TERMINAL_STATES or an intermediate state such as SUBMITTED."""
    message: str | None = None
    parset: str | None = None
    """The parset built for a dry run."""
    sb_id: int | str | None = None
    """The Scheduling Block created for a real request."""

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL_STATES


class AtnfFacility(ABC):
    """
    Generic ATNF facility. The observatory accepts no inbound connections, so
    requests are put on a relay that it polls. Submitting returns at once and
    the outcome is read from the request status.
    """

    @abstractmethod
    def api_key(self, settings: Settings) -> str:
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def api_root(self, settings: Settings) -> str:
        raise NotImplementedError("Subclasses must implement this method")

    def __init__(
        self,
        settings: Settings = default_settings,
        transport: httpx.BaseTransport | None = None,
    ):
        headers = {"Authorization": f"Bearer {self.api_key(settings)}"}
        self.client: httpx.Client = httpx.Client(
            base_url=self.api_root(settings), headers=headers, transport=transport
        )

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    def validate_observation(self, observation: TargetRequest) -> dict[str, Any]:
        """Check a request locally and return the Scheduling Block parameters it
        sets. Rejects targets ATNF cannot observe."""
        return observation.to_sb_params()

    def submit_observation(
        self,
        observation: TargetRequest,
        request_id: str | None = None,
        dry_run: bool = False,
        expires: datetime | None = None,
    ) -> str:
        """Queue a request and return its id. Submitting again with the same id
        does not queue it twice. A dry run builds the parset without submitting
        it. A request is not acted on after `expires`.
        """
        observation.to_sb_params()
        if expires is not None and expires.tzinfo is None:
            raise ValueError("expires must be timezone aware")
        request_id = request_id or str(uuid.uuid4())
        payload: dict[str, Any] = {
            "mode": observation.mode,
            "dry_run": dry_run,
            "request": observation.model_dump(mode="json", exclude_none=True),
        }
        if expires is not None:
            payload["expires"] = expires.isoformat()
        self._send("PUT", f"requests/{request_id}", json=payload)
        return request_id

    def get_observation_status(self, request_id: str) -> ObservationStatus:
        response = self._send("GET", f"requests/{request_id}")
        try:
            return ObservationStatus.model_validate(response.json())
        except ValueError as e:
            raise AtnfNetworkError(f"Unusable status for {request_id}") from e

    def cancel_observation(self, request_id: str) -> bool:
        """Cancel a request. Returns False if the observatory already has it."""
        response = self._send("DELETE", f"requests/{request_id}", allow=(409,))
        return response.status_code != 409

    def _send(
        self, method: str, path: str, allow: tuple[int, ...] = (), **kwargs: Any
    ) -> httpx.Response:
        try:
            response = self.client.request(method, path, **kwargs)
        except httpx.HTTPError as e:
            raise AtnfNetworkError(f"Could not reach the ATNF relay for {path}") from e
        if response.is_success or response.status_code in allow:
            return response
        if response.status_code in (401, 403):
            raise AuthenticationError(f"ATNF relay: {response.content}")
        raise AtnfNetworkError(f"ATNF relay returned {response.status_code} for {path}")
