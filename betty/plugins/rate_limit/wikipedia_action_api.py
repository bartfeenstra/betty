"""
The Wikipedia action API rate limit.
"""

import re
from typing import Final

from betty.http_client.rate_limit import RateLimitDefinition

# See https://www.mediawiki.org/wiki/API:Action_API.
WIKIPEDIA_ACTION_API: Final[RateLimitDefinition] = RateLimitDefinition(
    "wikipedia-action-api",
    limit=(200, 1),
    # https://www.mediawiki.org/wiki/API:Etiquette states there are no hard limits on the Wikimedia
    # Foundation-managed Action APIs. We've taken the limit of "200 requests per second" from
    # https://www.mediawiki.org/wiki/Wikimedia_REST_API#Terms_and_conditions instead.
    match=re.compile(r"^https?://[a-z\-]+\.wikipedia\.org/w/api\.php(.*?)$"),
)
