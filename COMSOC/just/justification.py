from COMSOC.interfaces.axioms import Instance, Axiom
from COMSOC.reasoning import AbstractReasoner

from typing import Set, List
from collections import deque

class Justification:

    """Class representing a justifcation for the outcome of some collective decision."""
    
    def __init__(self, problem, normative: Set[Axiom], explanation: Set[Instance]):
        """Given a justification problem, a set of axioms and an explanation, construct a justification object."""
        self._normative = normative
        self._explanation = explanation
        self._problem = problem

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

    def __str__(self):
        res = f"########\n{self.problem}\n\nNORMATIVE BASIS:\n\t{{{', '.join(map(str, self.normative))}}}\nEXPLANATION:\n"
        for instance in sorted(self.explanation, key = lambda instance: str(instance.created_by)):
            res += "\t(" + str(instance.created_by).upper() + ") " + str(instance) + "\n"

        return res + "########"

    def __len__(self):
        return len(self._explanation)