"""Art provider integration boundary for sticker generation.

LOOP5.6A keeps this module as an importable placeholder only. Concrete remote
provider adapters belong in a later strategy implementation loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ArtProviderResult:
    provider: str
    ok: bool
    payload: dict[str, Any]
    error: str | None = None


class ArtProviderUnavailable(RuntimeError):
    """Raised when no configured art provider can handle a request."""


def generate_art(_request: dict[str, Any]) -> ArtProviderResult:
    """Return an explicit unavailable result until provider adapters are wired."""
    return ArtProviderResult(
        provider="unconfigured",
        ok=False,
        payload={},
        error="Art provider adapters are not configured in LOOP5.6A.",
    )
