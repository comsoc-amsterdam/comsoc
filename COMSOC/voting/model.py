from COMSOC.interfaces.model import AbstractScenario, AbstractPreference, AbstractOutcome, AbstractProfile
from typing import Tuple, Dict, Set, Iterator

# todo: scenario, profile

class VotingPreference(AbstractPreference, tuple):
    """Class representing an individual preference in voting. Extends a tuple."""

    def __init__(self, preference):
        """Initialise the preference by passing an (ordered) sequence of integers."""
        tuple.__init__(preference)

    def top(self) -> int:
        """Return the top alternative in this order."""
        return self[0]

    def prefers(self, x, y) -> bool:
        """Check whether alternative x is better than y in this order."""
        return self.index(x) < self.index(y)

    def rank(self, x) -> int:
        """Return the rank of alternative x. Goes from 1 to m, where m is the number of alternatives."""
        return self.index(x) + 1

    def __str__(self):
        return '>'.join(map(str, self))

class VotingOutcome(AbstractOutcome, frozenset):
    """Class representing a voting outcome: set of alternatives. Extends a frozenset."""

    def __init__(self, outcome):
        """Initialise the outcome by passing a collection of integers."""
        frozenset.__init__(outcome)

    def __str__(self):
        return '{' + ', '.join(map(str, sorted(self))) + '}'

    def asp_fact(self):
        return 'o' + ','.join(map(str, sorted(self)))