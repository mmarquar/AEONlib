from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel

from aeonlib.atnf.models import TargetRequest
from aeonlib.exceptions import AuthenticationError, ServiceNetworkError

TERMINAL_STATES = frozenset({"VALIDATED", "OBSERVED", "FAILED", "CANCELLED", "EXPIRED"})
"""States a request never leaves."""


class AtnfNetworkError(ServiceNetworkError):
    pass


class ObservationStatus(BaseModel):
    """Where a request has got to, as reported by the relay."""

    state: str
    """PENDING until the observatory picks the request up, then one of
    ``TERMINAL_STATES`` or an intermediate state such as SUBMITTED."""
    message: str | None = None
    parset: str | None = None
    """The parset built for a dry run."""
    sb_id: int | str | None = None
    """The Scheduling Block created for a real request."""

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL_STATES


class AtnfFacility:
    """Shared client for ATNF requests, which are queued, not delivered.

    The observatory cannot be called from outside, so requests go to a relay
    that both sides can reach. The observatory polls the relay, acts on what it
    finds and posts the outcome back. ``submit_observation`` therefore returns
    a ticket at once, and ``get_observation_status`` reports progress.

    Use a telescope subclass, which reads that telescope's settings.
    """

    def __init__(self, api_root: str, token: str):
        self._client = httpx.Client(
            base_url=api_root.rstrip("/") + "/",
            headers={"Authorization": f"Bearer {token}"},
        )

    def close(self) -> None:
        self._client.close()

    def validate_observation(self, observation: TargetRequest) -> dict[str, Any]:
        """Check a request locally and return the SB parameters it sets.

        Makes no network call. Limits and allowed values were enforced when the
        request was built, and this also rejects targets ATNF cannot take.
        """
        return observation.to_sb_params()

    def submit_observation(
        self,
        observation: TargetRequest,
        *,
        dry_run: bool = False,
        expires: datetime | None = None,
    ) -> str:
        """Queue a request and return its ticket.

        A dry run makes the observatory build the parset without submitting
        anything; read it from ``get_observation_status``. ``expires`` (timezone
        aware) stops a stale request being acted on if it waits too long.
        """
        observation.to_sb_params()  # fail on unsupported targets before any call
        body: dict[str, Any] = {
            "mode": observation.mode,
            "dry_run": dry_run,
            "request": observation.model_dump(mode="json", exclude_none=True),
        }
        if expires is not None:
            if expires.tzinfo is None:
                raise ValueError("expires must be timezone aware")
            body["expires"] = expires.isoformat()
        response = self._send("POST", "requests", json=body)
        return str(self._field(response, "requests", "id"))

    def get_observation_status(self, ticket: str) -> ObservationStatus:
        """Return the state of a queued request."""
        path = f"requests/{ticket}"
        response = self._send("GET", path)
        try:
            return ObservationStatus.model_validate(response.json())
        except ValueError as exc:
            raise AtnfNetworkError(f"Unusable response on {path}") from exc

    def cancel_observation(self, ticket: str) -> bool:
        """Cancel a request, returning False if it is already being acted on.

        The observatory sees the cancellation on its next poll.
        """
        response = self._send("DELETE", f"requests/{ticket}", allow={409})
        return response.status_code != 409

    def _send(
        self, method: str, path: str, *, allow: set[int] | None = None, **kwargs: Any
    ) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise AtnfNetworkError(f"Could not reach the ATNF relay on {path}") from exc
        if response.is_success or response.status_code in (allow or ()):
            return response
        if response.status_code in (401, 403):
            raise AuthenticationError("ATNF relay rejected the token")
        raise AtnfNetworkError(f"ATNF relay error {response.status_code} on {path}")

    @staticmethod
    def _field(response: httpx.Response, path: str, key: str) -> Any:
        try:
            return response.json()[key]
        except (ValueError, KeyError, TypeError) as exc:
            raise AtnfNetworkError(f"Unusable response on {path}") from exc
