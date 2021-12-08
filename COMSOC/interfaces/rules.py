from COMSOC.interfaces.model import AbstractProfile, AbstractOutcome, AbstractScenario
from abc import ABC, abstractmethod
from typing import List, Callable

class AbstractRule(ABC):
    """Abstract rule class."""

    @classmethod
    def from_function(cls, func: Callable, *args):

        """Return a rule constructed from an input function."""

        class NamelessRule(cls):
            def __call__(self, profile):
                return func(profile)

        return NamelessRule(*args)

    def __init__(self, scenario: AbstractScenario):
        self._scenario = scenario
        self._string = None

    @property
    def scenario(self):
        return self._scenario
    

    @abstractmethod
    def __call__(profile: AbstractProfile) -> AbstractOutcome:
        """Return the result of the rule."""
        pass

    @abstractmethod
    def as_SAT(self) -> List[int]:
        """Return this rule as a SAT model."""
        pass

    def __str__(self):
        if self._string is None:
            self._string = "#############################\n"
            for profile in sorted(self.scenario.profiles):
                self._string += f"F({profile}) ---> {self(profile)}\n"
            self._string += "#############################"

        return self._string

    def __eq__(self, other):
        return type(self) == type(other) and self.scenario == other.scenario