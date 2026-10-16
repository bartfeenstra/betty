"""
Reusable dictionaries.
"""

from typing import final


class _Dict:
    pass


# @todo Subclass all the mutable mapping base classes
# @todo
# @todo
@final
class Dict(_Dict):
    pass


# @todo Subclass only the immutable mapping base classes
# @todo
# @todo
@final
class FrozenDict(_Dict):
    pass
