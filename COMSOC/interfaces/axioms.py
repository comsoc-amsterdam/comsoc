from typing import Set, List, Type
from COMSOC.interfaces.model import AbstractScenario, AbstractProfile
from abc import ABC, abstractmethod

class Axiom(ABC):

    """Abstract class representing a generic axiom."""

    def __init__(self, scenario: AbstractScenario):
        """Initialise this axiom for a specific scenario."""
        self._scenario = scenario

    def as_SAT(self, encoding):

        """Return this axiom as SAT."""

        cnf = []

        for instance in self.getInstances():
            cnf += instance.as_SAT(encoding)

        return cnf   

    @property
    def scenario(self):
        """Return the reference scenario."""
        return self._scenario
    
    @abstractmethod
    def getInstances(self) -> Set:
        """Return all instances of this axiom."""
        pass

    @abstractmethod
    def getInstancesMentioning(self, profile: AbstractProfile) -> Set:
        """Return all instances of this axiom mentioning a specific profile."""
        pass

    def getInstancesMentioningHeuristic(self, profile: AbstractProfile, heur_info: dict=None):
        """Return some instances of this axiom mentioning this profile according to some heuristic strategy.

        Accepts a dictionary of heuristic information (the exact definition of this dictionary depends on the heuristic used).
        By default, just use the default strategy."""
        return self.getInstancesMentioning(profile)

    def __eq__(self, other):
        return type(self) == type(other) and self.scenario == other.scenario

    def __str__(self):
        """Return the name of the axiom as a string."""
        return type(self).__name__

    def __hash__(self):
        # Name of axiom and scenario.
        return hash((str(self), self.scenario))

class IntraprofileAxiom(Axiom):

    """Axiom whose instances must mention only one profile."""

    #@final
    def isIntra(self):
        return True

class InterprofileAxiom(Axiom):

    """Axiom whose instances might mention more than one profile."""

    #@final
    def isIntra(self):
        return False

class Instance(ABC):

    """Class representing an axiom instance."""
    
    @property
    @abstractmethod
    def axiom(self) -> Type[Axiom]:
        """Return the class of the axiom which this instance is instance of."""
        pass

    @property
    def axiom_name(self):
        return self.axiom.__name__

    @abstractmethod
    def mentions(self) -> Set[AbstractProfile]:
        """Return the set of profiles mentioned by this instance."""
        pass

    #@final
    def __eq__(self, other):
        """Check whether this instance is equal to some other.

        Equality holds if the two instances are of the same axiom and if some other conditions hold (defined in the _isEqual() method).
        """
        return type(self) == type(other) and self._isEqual(other)

    @abstractmethod
    def _isEqual(self, other) -> bool:
        """Defines the condition for equality between two instances of this axiom.

        Note: the fact that these are instance of the same axiom is already taken care of in __eq__. Don't do that!"""
        pass

    #@final
    def __hash__(self):
        return hash((type(self), self._hashable()))

    @abstractmethod
    def _hashable(self):
        """Return some information for hashing purposes. Must be compatible with _isEqual().

        Note: the axiom name is already taken care by the __hash__ function. Don't enforce that."""
        pass

    @abstractmethod
    def __str__(self):
        """A description of this instance."""
        pass

    @abstractmethod
    def as_SAT(self, encoding) -> List[List[int]]:
        """Return the SAT encoding of this instance."""
        pass