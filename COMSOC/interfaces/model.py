from abc import ABC, abstractmethod
from typing import Iterator, Callable, List, Set

class AbstractScenario(ABC):
    """Abstract interface representing an aggregation scenario"""

    def __init__(self):
        raise NotImplementedError("Implement me!")

    @property
    def defaultAxioms(self) -> Set:
        """Return the default axioms that represent fundamental properties of this scenario.

        For example, that at least one alternative must be elected in every voting scenario.""" 
        # Override me!
        return set()

    @property
    @abstractmethod
    def theory(self):
        """Return the theory (module) this scenario is part of."""
        pass

    @property
    @abstractmethod
    def nProfiles(self) -> int:
        """Return the number of profiles in this scenario."""
        pass

    @property
    @abstractmethod
    def profiles(self) -> Iterator:
        """Return an iterator over all profiles of this scenario."""
        pass

    @abstractmethod
    def get_profile(self, description: str):
        """Return a profile corresponding to the input string."""
        pass

    @abstractmethod
    def get_outcome(self, description: str):
        """Return an outcome corresponding to the input string."""
        pass
        
    @property
    @abstractmethod
    def preferences(self) -> Iterator:
        """Return an iterator over all possible preferences of this scenario."""
        pass

    @property
    @abstractmethod
    def outcomes(self) -> Iterator:
        """Return an iterator over all possible outcomes of this scenario."""
        pass

    @abstractmethod
    def __str__(self):
        pass

class AbstractPreference(ABC):
    """Abstract interface representing an individual preference."""

    @abstractmethod
    def __init__(self):
        pass

class AbstractOutcome(ABC):
    """Abstract interface representing an aggregation outcome."""

    @abstractmethod
    def __init__(self):
        pass

class AbstractProfile(ABC):
    """Abstract interface representing a preference profile."""

    @abstractmethod
    def __init__(self):
        """Initialise the profile."""
        pass