"""Export tools to reason about social choice axioms in various encoding languages."""

from abc import ABC, abstractmethod

from COMSOC.interfaces.axioms import Axiom, Instance
from COMSOC.interfaces.model import AbstractScenario
from COMSOC.interfaces.rules import AbstractRule

from typing import Set, Type, Iterator, List
import os
from pysat.solvers import Minisat22 as pySAT

from time import time

from COMSOC.MARCO.src.marco.marco import parse_args, enumerate_with_args

class AbstractReasoner(ABC):

    """Abstract interface that describes the methods offered by a reasoner.

    A reasoner is a collection of methods that handle tasks such as encoding, testing for satisfiability, and MUS enumeration."""

    def getScenario(self, axioms: Set[Axiom]):
        """Return the scenario of the set of axioms given.

        If the axioms are defined for different scenarios, raise an Exception."""

        scenario = None

        for axiom in axioms:
            if scenario is None:
                scenario = axiom.scenario
            elif scenario != axiom.scenario:
                raise ValueError("All axioms must regard the same scenario.")

        return scenario

    #@final
    @abstractmethod
    def encodeAxioms(self, axioms: Set[Axiom]):
        """Given a set of instances, encode them in the given language."""
        pass

    @abstractmethod
    def encodeInstances(self, instances: Set[Instance]):
        """Given a set of axioms, encode them in the given language."""
        pass

    @abstractmethod
    def _isSatisfiable(self, encoded_thing) -> bool:
        """Check if an encoded object is satisfiable."""
        pass

    @abstractmethod
    def _getRule(self, scenario, encoded_thing) -> AbstractRule:
        """Return an aggregation function (for the input scenario) that satisfies the input axiom instances."""
        pass

    #@final
    def checkInstances(self, instances: Set[Instance]) -> bool:

        return self._isSatisfiable(self.encodeInstances(instances))

    #@final
    def checkAxioms(self, axioms: Set[Type[Instance]]) -> bool:

        """Check whether the input axioms (for the input scenario) are satisfiable."""
        return self._isSatisfiable(self.encodeAxioms(axioms))

    #@final
    def findRule(self, axioms: Set[Type[Instance]]) -> AbstractRule:

        scenario = self.getScenario(axioms)

        """Return an aggregation function (for the input scenario) that satisfies the input axiom instances."""
        return self._getRule(scenario, self.encodeAxioms(axioms))

    @abstractmethod
    def enumerateMUSes(self, instances: Set[Instance]) -> Iterator[Set[Instance]]:

        """Enumerate the subsets of that input instances that are minimally unsatisfiable.

            Parameters
            ----------
            instances : Set[Instance]
                A set of instances.

            Returns
            -------
            Iterator
                An iterator over sets of instances.
        """

        pass

    @abstractmethod
    def _doesRuleSatisfy(self, encoded_thing, rule: AbstractRule) -> bool:
        pass

    
    #@final
    def checkRule(self, axioms: Set[Type[Instance]], rule: AbstractRule) -> bool:
        """Check whether an aggregation rule (for a given scenario) satisfies the input axioms."""
        return self._doesRuleSatisfy(self.encodeAxioms(axioms), rule)

class SAT(AbstractReasoner):

    """SAT reasoner. See the AbstractReasoner class for more details."""

    def __init__(self, encoding):
        self._encoding = encoding
        # The SAT reasoner communicates with the MUS enumerator through a text file. We declare here its name.
        self.FILE_NAME = f"dump_{time()}.gcnf"

    @property
    def encoding(self):
        return self._encoding
    
    def encodeInstances(self, instances: Set[Instance]):
        cnf = []
        for instance in instances:
            cnf += instance.as_SAT(self.encoding)
        return cnf

    
    def encodeAxioms(self, axioms):
        cnf = []
        for axiom in axioms:
            cnf += axiom.as_SAT(self.encoding)
        return cnf

    
    def _isSatisfiable(self, cnf: List[List[int]]) -> bool:
        """Check whether a cnf (list of lists of non-zero integers) is satisfiable."""
        with pySAT(bootstrap_with = cnf) as l:
            solvable = l.solve()
        return solvable

    
    def _getModel(self, cnf: List[List[int]]) -> List[int]:
        """Given a (satisfiable) cnf, return a model (list of literals)."""

        with pySAT(bootstrap_with = cnf) as l:
            l.solve()
            model = l.get_model()
        return model

    
    def _getRule(self, scenario, cnf) -> AbstractRule:

        # Get an assignment satysfing the input instances.
        model = self._getModel(cnf)
        # Decode them.
        return scenario.decodeSATModel(model) if model is not None else None

    
    def _doesRuleSatisfy(self, cnf, rule: AbstractRule) -> bool:
        # First, we encode the rule as a list of literals (describing which alternatives win in which scenarios).
        # Then, we append, to the instances-cnf, a clause for every such literal.
        for literal in rule.as_SAT(self.encoding):
            cnf.append([literal])

        # The resulting cnf is satisfiable iff the SCF satisfies the instances.

        return self._isSatisfiable(cnf)

    
    def enumerateMUSes(self, instances: Set[Instance]) -> Iterator[Set[Instance]]:

        # First, we assign, to each instance, a unique index.
        # Note that MARCO (our MUS enumerator) requires to index CNFs starting from one. Hence the +1.
        indexed_instances = {i+1:instance for i, instance in enumerate(instances)}

        # Then, we encode said uniquely-indexed instances as a DIMACS-style gCNF (group CNF).
        # See https://people.sc.fsu.edu/~jburkardt/data/cnf/cnf.html for more details.
        gcnf_string = self._getGCNF(indexed_instances)

        try:
            # The "x" option creates a file, and throws an error if the file already exists.
            # We do this because at the end of the execution we remove the file, and we do not want to delete pre-existing files...
            file = open(self.FILE_NAME, "x")
            file.write(gcnf_string)
            file.close()

            marco_args_list = [self.FILE_NAME, '--verbose', '--bias', 'MUSes']

            marco_args = parse_args(marco_args_list)
            # generator can be saved in a variable to call .close() later
            marco_gen = enumerate_with_args(marco_args)

            # Every line of the output of the subprocess is an MUS.
            for result in marco_gen:
                # Only care for MUSes (first argument is `U`)
                kind, indexes = result
                if kind == 'U':
                    # We return the instances corresponding to the group of clauses in the gMUS.
                    # Recall that we use the same indexes for instances and group of clauses, so this works.
                    yield {indexed_instances[i] for i in indexes}

        finally:
            # Close the generator.
            marco_gen.close()
            # Remove the created file.
            os.remove(self.FILE_NAME)


    
    def _getGCNF(self, indexed_instances):

        """Encode a set of (indexed) instances as a DIMACS-style group CNF.

            Parameters
            ----------
            indexed_instances : Dict[int, Instance]
                A dictionary mapping integers to instances.

            Returns
            -------
            str
                A DIMACS-style group CNF (gcnf). The indexes of the clauses in this file match the indexes in the indexed_instances object.
        """

        # Get the (indexed) cnfs.
        indexed_cnfs = {i:inst.as_SAT(self.encoding) for i, inst in indexed_instances.items()}

        # Count the number of unique propositional variables.
        variables = set()
        for cnf in indexed_cnfs.values():
            for clause in cnf:
                # We get the absolute values because we only care about the variables, not the literals.
                variables.update(map(abs, clause))

        new_var = {var:i+1 for i, var in enumerate(variables)}

        for index, cnf in indexed_cnfs.items():
            new_cnf = []
            for clause in cnf:
                new_clause = [(1 if val>0 else -1)*new_var[abs(val)] for val in clause]
                new_cnf.append(new_clause)
            indexed_cnfs[index] = new_cnf

        nVariables = len(variables)
        nGroups = len(indexed_cnfs)
        nClauses   = sum(map(len, indexed_cnfs.values()))

        # file header
        gcnf_string = "p gcnf " + str(nVariables) + " " + str(nClauses) + " " + str(nGroups) + "\n"

        for index in indexed_instances.keys():
            # encode each instance (group of clauses)
            # in DIMACS-style gCNFS, we need to assign a unique index to every group of clauses.
            for clause in indexed_cnfs[index]:
                line = f"{{{index}}} "
                for literal in clause:
                    line += f"{literal} "
                line += "0 \n"
                gcnf_string += line

        return gcnf_string