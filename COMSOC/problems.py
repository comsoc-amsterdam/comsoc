from COMSOC.reasoning import SAT
from COMSOC.interfaces.model import AbstractScenario, AbstractProfile, AbstractOutcome
from COMSOC.interfaces.axioms import Axiom, Instance

from typing import Set, Iterator

from COMSOC.just.generation import InstanceGraph
from COMSOC.just.justification import Justification
from COMSOC.just.axioms import GoalConstraint
from COMSOC.just.axioms import DerivedAxiomInstance

from abc import ABC, abstractmethod

class AbstractProblem(ABC):
    """Generic reasoning problem."""

    def __init__(self):
        self._past_solutions = {}
        self._dispatch_strategies = {}

        for attribute in dir(self):
            if attribute[:9] == 'strategy_':
                self._dispatch_strategies[attribute[9:]] = getattr(self, attribute)

    def getScenario(self, axioms: Set[Axiom]):
        """Return the scenario of the set of axioms given."""

        scenario = None

        for axiom in axioms:
            if scenario is None:
                scenario = axiom.scenario
            elif scenario != axiom.scenario:
                raise ValueError("All axioms must regard the same scenario.")

        return scenario

    def _get_solution_key(self, dictionary):
        return frozenset((key, value) for key, value in dictionary.items() if key != "strategy")

    def solve(self, **kwargs):
        try:
            sol_key = self._get_solution_key(kwargs)

            if not sol_key in self._past_solutions:
                if "strategy" not in kwargs:
                    raise ValueError("Please specify a strategy. Usage: `strategy=<strategy_name>`.\n" + \
                        f". Available strategies: {','.join(strategy for strategy in self._strategies)}")

                strategy = kwargs["strategy"]
                cleaned_kwargs = dict(sol_key)
                self._past_solutions[sol_key] = self._dispatch_strategies[strategy](**cleaned_kwargs)
            return self._past_solutions[sol_key]

        except KeyError:
            raise ValueError(f"The selected strategy `{kwargs['strategy']}` was not implemented.\n" + \
                f". Available strategies: {','.join(strategy for strategy in self._strategies)}")    

class CheckAxioms(AbstractProblem):

    def __init__(self, axioms):
        super().__init__()
        self._axioms = axioms

    def strategy_SAT(self):
        scenario = self.getScenario(self._axioms)
        reasoner = SAT(scenario.SATencoding)
        return reasoner.checkAxioms(self._axioms)

class CheckRule(AbstractProblem):

    def __init__(self, axioms, rule):
        super().__init__()
        self._axioms = axioms
        self._rule = rule

    def strategy_SAT(self):
        scenario = self.getScenario(self._axioms)
        if self._rule.scenario != scenario:
            raise ValueError("The rule and the axioms regard different scenarios.")

        reasoner = SAT(scenario.SATencoding)
        return reasoner.checkRule(self._axioms, self._rule)

class FindRule(AbstractProblem):

    def __init__(self, axioms):
        super().__init__()
        self._axioms = axioms

    def strategy_SAT(self):
        scenario = self.getScenario(self._axioms)
        reasoner = SAT(scenario.SATencoding)
        return reasoner.findRule(self._axioms)

class JustificationProblem(AbstractProblem):

    """Class representing a justification problem."""

    def __init__(self, profile: AbstractProfile,\
            outcome: AbstractOutcome, corpus: Set[Axiom]):

        """Construct a justification problem object."""

        super().__init__()

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

    def _extract(self, instances: Set[Instance], reasoner, ignore_nontriviality : bool) -> Iterator:
        """Given a set of instances and a reasoner, iterate over the justification that can be extracted from this set of instances."""

        # Add the goal constraint to the instances.
        goal = GoalConstraint(self.scenario, self.profile, self.outcome)
        instances.add(goal)

        # If the set of instances is unsatisfiable, it might contain a justification.
        if not reasoner.checkInstances(instances):

            # Enumerate all MUSes of these instances...
            for MUS in reasoner.enumerateMUSes(instances):

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
                    if ignore_nontriviality or solver.checkAxioms(normative):
                        yield Justification(self, normative, explanation)
                except KeyError:
                    # We handle by doing nothing. Indeed, we will just continue iterating over the MUSes.
                    pass

    def _justify(self, reasoner, depth: int=None, heuristics: bool=False,\
        maximum: int=-1, derivedAxioms = set(), ignore_nontriviality = False) -> Iterator:

        """Iterate over the justifications for this problem.

            Parameters
            ----------
            solver : AbstractReasoner
                The reasoner used to handle the solving step.
            depth : int
                Maximum depth possible. Default: None (no constraint).
            heuristics : bool
                Whether to use the heuristic strategies. Default: False
            maximum : int
                How many justifications to retrieve.
            derivedAxioms : set
                Heuristic axioms to add.
            ignore_nontriviality : bool
                If set to true, does not perform the nontriviality check on the resulting basis.

            Returns
            -------
            Iterator
                An iterator over sets justifications.
        """

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

        results = []

        # Recall that BFS iterates over the sets of instances in order of depth. That is, at the first iteration,
        # returns all instances up to depth 0; then up to depth 1; etc...
        for instances in graph.BFS(self.profile, depth):
            # Try to extract a justification from these instances:
            for justification in self._extract(instances, reasoner, ignore_nontriviality):
                # if we find one, yield it
                results.append(justification)

                if len(results) == maximum:
                    return results
                    
        return results

    def strategy_SAT(self, **kwargs):
        reasoner = SAT(self.scenario.SATencoding)
        return self._justify(reasoner = reasoner, **kwargs)
    
    def __str__(self):
        return f"Given profile: {self.profile}\nTarget outcome: {self.outcome}\nCorpus: {{{', '.join(map(str, self.corpus))}}}"
