from COMSOC.interfaces.axioms import Instance, Axiom
from COMSOC.interfaces.model import AbstractProfile

from COMSOC.anonymous.model import AnonymousScenario

from typing import Type, Set

class AbstractGoalConstraint(Instance):

    """Class representing the fact that some outcome must not hold in a profile."""

    def __init__(self, profile, outcome):
        self._profile = profile
        self._outcome = outcome

    @property
    def profile(self):
        return self._profile

    @property
    def axiom(self) -> Type[Axiom]:
        return None
    
    def mentions(self) -> Set[AbstractProfile]:
        """Return the set of profiles mentioned by this instance."""
        return set(self._profile)

    def _isEqual(self, other) -> bool:
        """Defines the condition for equality between two instances of this axiom."""

        return self._profile == other._profile and self._outcome == other._outcome

    def _hashable(self):
        """Return some information for hashing purposes. Must be compatible with _isEqual().

        Note: the axiom name is already taken care by the __hash__ function. Don't enforce that."""
        return (self._profile, self._outcome)

    def __str__(self):
        """A description of this instance."""
        return f"In profile {self._profile} the outcome should NOT be {self._outcome}."


class AnonymousGoal(AbstractGoalConstraint):

    def as_SAT(self, encoding):
        p, o = self._profile, self._outcome
        return [[encoding.encode(p, a) if a not in o else -encoding.encode(p, a) for a in self.profile.alternatives]]    

def GoalConstraint(scenario, profile, outcome):
    return {
        AnonymousScenario : AnonymousGoal
    }[scenario.__class__](profile, outcome)