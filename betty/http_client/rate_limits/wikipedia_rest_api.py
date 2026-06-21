"""
The Wikipedia REST API rate limit.
"""

from __future__ import annotations

import re
from typing import Final

from betty.http_client.rate_limit import RateLimitDefinition

# See https://www.mediawiki.org/wiki/Wikimedia_REST_API#Terms_and_conditions.
WIKIPEDIA_REST_API: Final[RateLimitDefinition] = RateLimitDefinition(
    "wikipedia-rest-api",
    limit=(200, 1),
    match=re.compile(r"^https?://[a-z\-]+\.wikipedia\.org/api/rest_v1(.*?)$"),
)
