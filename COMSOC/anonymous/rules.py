from COMSOC.interfaces.rules import AbstractRule

import COMSOC.anonymous.model as model

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List

class AnonymousRule(AbstractRule, ABC):
    """Abstract rule class."""

    def __init__(self, scenario):
        super().__init__(scenario)

        self._model = None

    #@final
    def as_SAT(self, encoding) -> List[int]:
        """Return this rule as a SAT model."""
        
        if self._model is None:
            self._model = []
            # For every profile, get the outcome.
            for profile in self.scenario.profiles:
                outcome = self(profile)
                # For every alternative, 
                for alt in self.scenario.alternatives:
                    # Encode this (profile, alternative) pair and
                    literal = encoding.encode(profile, alt)
                    # If it wins, add a positive literal, negative otherwise.
                    self._model.append(literal if alt in outcome else -literal)

        return self._model

class ScoringRule(AnonymousRule, ABC):

    @abstractmethod
    def _get_score(self, ballot, alternative):
        pass

    def __call__(self, profile):

        scores = defaultdict(int)

        # For every ballot, compute the points this ballot assigns to each alternative
        # (multiplied by the number of voters expressing this ballot)
        for ballot, count in profile.ballotsWithCounts():

            for alternative in ballot:
                scores[alternative] += self._get_score(ballot, alternative) * count

        # get the alternative(s) with highest score

        winners = set()
        maxscore = -float("inf")

        for alternative, score in scores.items():
            if score > maxscore:
                winners = {alternative}
                maxscore = score
            elif score == maxscore:
                winners.add(alternative)

        return model.AnonymousOutcome(winners)

class Borda(ScoringRule):
    """The Borda rule."""

    def _get_score(self, ballot, alternative):
        rank = ballot.index(alternative)
        return (len(ballot) - rank - 1)

class Plurality(ScoringRule):
    """The Borda rule."""

    def _get_score(self, ballot, alternative):
        rank = ballot.index(alternative)
        return 1 if rank == 0 else 0