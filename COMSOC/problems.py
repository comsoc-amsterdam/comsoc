from COMSOC.reasoning import SAT
from COMSOC.interfaces.model import AbstractScenario, AbstractProfile, AbstractOutcome
from COMSOC.interfaces.axioms import Axiom, Instance, DerivedAxiomInstance

from typing import Set, Iterator

from COMSOC.justification import Justification, InstanceGraph

class AbstractProblem:
    """Generic reasoning problem."""
    def getScenario(self, axioms: Set[Axiom]):
        for anyAxiom in axioms:
            scenario = anyAxiom.scenario
            break

        for axiom in axioms:
            if scenario != axiom.scenario:
                raise ValueError("All axioms must regard the same scenario.")

        return scenario

class ReasoningProblem(AbstractProblem):

    def __init__(self, strategies: dict):
        self._past_solutions = {}
        self._dispatch_strategies = strategies

    def _get_solution_key(self, dictionary):
        return frozenset((key, value) for key, value in dictionary.items() if key != "strategy")

    def solve(self, **named_args):
        try:
            sol_key = self._get_solution_key(named_args)

            if not sol_key in self._past_solutions:
                if "strategy" not in named_args:
                    raise ValueError("Please specify a strategy. Usage: `strategy=<strategy_name>`.\n" + \
                        f". Available strategies: {','.join(strategy for strategy in self._strategies)}")

                strategy = named_args["strategy"]
                cleaned_named_args = dict(sol_key)
                self._past_solutions[sol_key] = self._dispatch_strategies[strategy](**cleaned_named_args)
            return self._past_solutions[sol_key]

        except KeyError:
            raise ValueError(f"The selected strategy `{kwargs['strategy']}` was not implemented.\n" + \
                f". Available strategies: {','.join(strategy for strategy in self._strategies)}")

class CheckAxioms(ReasoningProblem):

    def __init__(self, axioms):

        scenario = self.getScenario(axioms)

        SATreasoner = SAT(scenario.theory.SATencoding)

        strategies = {
            "SAT" : lambda : SATreasoner.checkAxioms(axioms)
        }

        super().__init__(strategies)

class CheckRule(ReasoningProblem):

    def __init__(self, axioms, rule):

        scenario = self.getScenario(axioms)

        SATreasoner = SAT(scenario.theory.SATencoding)

        strategies = {
            "SAT" : lambda : SATreasoner.checkRule(axioms, rule)
        }

        super().__init__(strategies)

class FindRule(ReasoningProblem):

    def __init__(self, axioms):

        scenario = self.getScenario(axioms)

        SATreasoner = SAT(scenario.theory.SATencoding)

        strategies = {
            "SAT" : lambda : SATreasoner.findRule(axioms)
        }

        super().__init__(strategies)

class JustificationProblem(AbstractProblem):

    """Class representing a justification problem."""

    def __init__(self, profile: AbstractProfile,\
            outcome: AbstractOutcome, corpus: Set[Axiom]):

        """Construct a justification problem object."""
        self._profile = profile
        self._outcome = outcome

        scenario = self.getScenario(corpus)

        self._theory = scenario.theory

        # We add the default axioms of the scenario. These are the properties that must always hold
        # for any aggregation rule. For example, in the case of voting, there is a default axiom 
        # stating that, for all profiles, at least one alternative should win.
        self._corpus = corpus.union(scenario.defaultAxioms)

        self._reasoners = {
            "SAT" : SAT(scenario.theory.SATencoding)
        }

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

    def _extract(self, instances: Set[Instance], strategy: str) -> Iterator:
        """Given a set of instances and a solver, iterate over the justification that can be extracted from this set of instances."""

        # Add the goal constraint to the instances.
        GoalConstraint = self._theory.axioms.GoalConstraint
        goal = GoalConstraint(self.profile, self.outcome)
        instances.add(goal)

        # If the set of instances is unsatisfiable, it might contain a justification.
        solver = self._reasoners[strategy]
        if not solver.checkInstances(instances):

            # Enumerate all MUSes of these instances...
            for MUS in solver.enumerateMUSes(instances):

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

                    # If the normative basis is nontrivial, yield the justification.
                    if solver.checkAxioms(normative):
                        yield Justification(self, normative, explanation)
                except KeyError:
                    # We handle by doing nothing. Indeed, we will just continue iterating over the MUSes.
                    pass

    def solve(self, strategy: str, depth: int=None, heuristics: bool=False, maximum: int=-1, derivedAxioms = set()) -> Iterator:

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

        # how many justifications we found so far?
        justsRetrievedSoFar = 0

        # Recall that BFS iterates over the sets of instances in order of depth. That is, at the first iteration,
        # returns all instances up to depth 0; then up to depth 1; etc...
        for instances in graph.BFS(self.profile, depth):
            # Try to extract a justification from these instances:
            for justification in self._extract(instances, strategy):
                # if we find one, yield it
                yield justification

                # Increase the counter, and quit if we reached the maximum allowed.
                # (maximum is -1 by default; in that case the condition will never be true.)
                justsRetrievedSoFar += 1
                if justsRetrievedSoFar == maximum:
                    return

    
    def __str__(self):
        return f"Given profile: {self.profile}\nTarget outcome: {self.outcome}\nCorpus: {{{', '.join(map(str, self.corpus))}}}"
