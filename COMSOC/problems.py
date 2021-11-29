from COMSOC.reasoning import SAT
from COMSOC.interfaces.model import AbstractScenario, AbstractProfile, AbstractOutcome
from COMSOC.interfaces.axioms import Axiom, Instance

from typing import Set, List, Iterator

from COMSOC.just.generation import InstanceGraph
from COMSOC.just.justification import Justification
from COMSOC.just.axioms import GoalConstraint
from COMSOC.just.axioms import DerivedAxiomInstance

from abc import ABC, abstractmethod

class AbstractProblem(ABC):
    """Generic reasoning problem."""

    def getScenario(self, axioms: Set[Axiom]):
        """Return the scenario of the set of axioms given."""

        scenario = None

        for axiom in axioms:
            if scenario is None:
                scenario = axiom.scenario
            elif scenario != axiom.scenario:
                raise ValueError("All axioms must regard the same scenario.")

        return scenario

class DecisionProblem(AbstractProblem):

    def __init__(self, axioms):
        self._axioms = axioms

    def solve(self, strategy):
        if not hasattr(self, "_solution"):
            self._solution = self._get_solution(self.get_reasoner(strategy))
        return self._solution

    def get_reasoner(self, strategy):
        if strategy == 'SAT':
            return SAT(self.getScenario(self._axioms).SATencoding)
        else:
            raise NotImplementedError("No such strategy", strategy)

    @abstractmethod
    def _get_solution(self, reasoner):
        pass

class CheckAxioms(DecisionProblem):

    def _get_solution(self, reasoner):
        return reasoner.checkAxioms(self._axioms)

class CheckRule(DecisionProblem):

    def __init__(self, axioms, rule):
        super().__init__(axioms)
        self._rule = rule

    def _get_solution(self, reasoner):
        return reasoner.checkRule(self._axioms, self._rule)

class FindRule(DecisionProblem):

    def __init__(self, axioms):
        self._axioms = axioms

    def _get_solution(self, reasoner):
        return reasoner.findRule(self._axioms)

class JustificationProblem(AbstractProblem):

    """Class representing a justification problem."""

    def __init__(self, profile: AbstractProfile,\
            outcome: AbstractOutcome, corpus: Set[Axiom]):

        """Construct a justification problem object."""

        self._profile = profile
        self._outcome = outcome
        self.scenario = self.getScenario(corpus)

        # We add the default axioms of the scenario. These are the properties that must always hold
        # for any aggregation rule. For example, in the case of voting, there is a default axiom 
        # stating that, for all profiles, at least one alternative should win.
        self._corpus = corpus.union(self.scenario.defaultAxioms)

    @property
    def profile(self):
        """Return the given profile."""
        return self._profile

    @property
    def outcome(self):
        """Return the target outcome."""
        return self._outcome
    
    @property
    def corpus(self):
        """Return the given set of axioms."""
        return self._corpus

    def _extract(self, instances: Set[Instance], extract_reasoner, \
            nontriviality_reasoner, ignore_nontriviality) -> Iterator:
        """Given a set of instances and a reasoner, iterate over the justification that can be extracted from this set of instances."""

        # Add the goal constraint to the instances.
        goal = GoalConstraint(self.scenario, self.profile, self.outcome)
        instances.add(goal)

        # If the set of instances is unsatisfiable, it might contain a justification.
        if not extract_reasoner.checkInstances(instances):

            # Enumerate all MUSes of these instances...
            for MUS in extract_reasoner.enumerateMUSes(instances):

                # An MUS is an explanation iff it contains the goal profile.

                try:

                    # We TRY to remove the gaol profile. Note that if this fails, it raises a KeyError, handled below.
                    MUS.remove(goal)

                    # Construct the explanation. It is made by the regular axiom instances, and for the derivedaxiom instances,
                    # by the instances of the axioms which imply them.

                    explanation = set()
                    for instance in MUS:
                        if isinstance(instance, DerivedAxiomInstance):
                            scenario = instance.created_by.scenario
                            instances = instance.convertToActivatorsInstances()
                            for instance in instances:
                                instance.created_by = instance.axiom(scenario)
                                explanation.add(instance)
                        else:
                            explanation.add(instance)

                    normative = {instance.created_by for instance in explanation}

                    # If the normative basis is nontrivial (or if we do not perform the check),
                    # yield the justification.
                    if ignore_nontriviality or nontriviality_reasoner.checkAxioms(normative):
                        yield Justification(self, normative, explanation)
                except KeyError:
                    # We handle by doing nothing. Indeed, we will just continue iterating over the MUSes.
                    pass

    def solve(self, extract: str, nontriviality: str, depth: int=None, heuristics: bool=False,\
        maximum: int=-1, derivedAxioms = set()) -> Iterator:

        """Iterate over the justifications for this problem.

            Parameters
            ----------
            extract : str
                Strategy to be used in the extraction phase.
            check : str
                Strategy to be used in the nontriviality check.
            depth : int
                Maximum depth possible. Default: None (no constraint).
            heuristics : bool
                Whether to use the heuristic strategies. Default: False
            maximum : int
                How many justifications to retrieve. Default: all.
            derivedAxioms : set
                Heuristic axioms to add. Default: none.

            Returns
            -------
            Iterator
                An iterator over justifications.
        """

        # Define the relevant reasoners.

        reasoners = {
            "SAT" : SAT(self.scenario.SATencoding)
        }

        extract_reasoner = reasoners[extract]

        if nontriviality == "ignore":
            ignore_nontriviality = True
            nontriviality_reasoner = None
        else:
            ignore_nontriviality = False
            nontriviality_reasoner = reasoners[extract]

        # Silly base case
        if maximum == 0:
            return

        # Which axioms we use? Well, those in the corpus, plus the axioms derived from the current corpus
        # Recall that all possible derived axioms are stored in Scenario.derivedAxioms (since axioms are scenario-dependent)

        axioms = set(self.corpus)
        if heuristics:
            for derived in derivedAxioms:
                if derived.isActive(self.corpus):
                    axioms.add(derived)

        graph = InstanceGraph(axioms, heuristics = heuristics)

        # how many justifications we found so far?
        justsRetrievedSoFar = 0

        # Recall that BFS iterates over the sets of instances in order of depth. That is, at the first iteration,
        # returns all instances up to depth 0; then up to depth 1; etc...
        for instances in graph.BFS(self.profile, depth):
            # Try to extract a justification from these instances:
            for justification in self._extract(instances, extract_reasoner, nontriviality_reasoner, ignore_nontriviality):
                # if we find one, yield it
                
                yield justification

                # Increase the counter, and quit if we reached the maximum allowed.
                # (maximum is -1 by default; in that case the condition will never be true.)
                justsRetrievedSoFar += 1
                if justsRetrievedSoFar == maximum:
                    return

    def __str__(self):
        return f"Given profile: {self.profile}\nTarget outcome: {self.outcome}\nCorpus: {{{', '.join(map(str, self.corpus))}}}"
