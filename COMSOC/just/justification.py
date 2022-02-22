from COMSOC.interfaces.axioms import Instance, Axiom
from COMSOC.reasoning import AbstractReasoner
from COMSOC.just.Trees.ASPTree import ASPTree
from COMSOC.just.Trees.displaytree.interface import DisplayTreeInterface

from typing import Set, List
from collections import deque

class Justification:

    """Class representing a justifcation for the outcome of some collective decision."""
    
    def __init__(self, problem, normative: Set[Axiom], explanation: Set[Instance]):
        """Given a justification problem, a set of axioms and an explanation, construct a justification object."""
        self._normative = normative
        self._explanation = explanation
        self._problem = problem

        self._scenario = None
        for axiom in normative:
            if self._scenario is None:
                self._scenario = axiom.scenario
            else:
                assert self._scenario == axiom.scenario

        # Check that the normative basis of this justification uses the allowed axioms.
        assert self._normative.issubset(problem.corpus), "Adequacy does not hold!"

    @property
    def problem(self):
        """Return the justification problem this justification solves."""
        return self._problem

    @property
    def normative(self):
        """Return the normative basis (set of axioms)."""
        return self._normative
    
    @property
    def explanation(self):
        """Return the explanation (set of instances)."""
        return self._explanation

    @property
    def goal(self):
        return self.problem.goal
    

    @property
    def scenario(self):
        return self._scenario

    @property
    def profile(self):
        return self.problem.profile
    
    @property
    def outcome(self):
        return self.problem.outcome
    

    @property
    def involved_profiles(self):
        if not hasattr(self, "_involved_profiles"):
            self._involved_profiles = set()
            for instance in self.explanation:
                self._involved_profiles.update(instance.mentions())

        return self._involved_profiles

    def __eq__(self, other):
        return self.normative == other.normative and self.explanation == other.explanation \
            and self.profile == other.profile and self.outcome == other.outcome

    def __str__(self):
        res = f"########\n{self.problem}\n\nNORMATIVE BASIS:\n\t{{{', '.join(map(str, self.normative))}}}\nEXPLANATION:\n"
        for instance in sorted(self.explanation, key = lambda inst: inst.axiom_name):
            res += "\t(" + instance.axiom_name.upper() + ") " + str(instance) + "\n"

        return res + "########"

    def __len__(self):
        return len(self._explanation)

    def displayASP(self, destination: str=None, strategy = "ASP", display = "dynamic", verbose = False):
        tree, encoding = ASPTree(self, limit = 1, verbose = verbose).getAProofTree()
        displayer = DisplayTreeInterface(tree, self, source = "ASP", encoding = encoding)
        return displayer.exportTree(display, dest = destination)