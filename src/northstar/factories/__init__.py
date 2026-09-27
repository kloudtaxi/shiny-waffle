"""Background population: Polyfactory builds the objects, Faker fills the values.

The background is noise around the hand-authored truth. It is seeded and fully
deterministic, and it is *policy-consistent*: every generated approval obeys the
pricing policy in force on its date, so the noise never contradicts the truth.
"""

from northstar.factories.background import SCALES, Background, build_background

__all__ = ["SCALES", "Background", "build_background"]
