from COMSOC.interfaces.axioms import Instance, Axiom, IntraprofileAxiom
from COMSOC.interfaces.model import AbstractProfile

from COMSOC.anonymous.axioms import NeutralityInstance
from COMSOC.anonymous.model import AnonymousScenario, AnonymousPreference

from typing import Type, Set, List

from abc import abstractmethod

###############
#             #
#    GOAL     #
#             #
###############

class AbstractGoalConstraint(Instance):

    """Class representing the fact that some outcome must not hold in a profile."""

    def __init__(self, profile, outcome):
        self._profile = profile
        self._outcome = outcome

    @property
    def profile(self):
        return self._profile

    @property
    def axiom(self) -> Type[Axiom]:
        return None
    
    def mentions(self) -> Set[AbstractProfile]:
        """Return the set of profiles mentioned by this instance."""
        return set(self._profile)

    def _isEqual(self, other) -> bool:
        """Defines the condition for equality between two instances of this axiom."""

        return self._profile == other._profile and self._outcome == other._outcome

    def _hashable(self):
        """Return some information for hashing purposes. Must be compatible with _isEqual().

        Note: the axiom name is already taken care by the __hash__ function. Don't enforce that."""
        return (self._profile, self._outcome)

    def __str__(self):
        """A description of this instance."""
        return f"In profile {self._profile} the outcome should NOT be {self._outcome}."


class AnonymousGoal(AbstractGoalConstraint):

    def as_SAT(self, encoding):
        p, o = self._profile, self._outcome
        return [[encoding.encode(p, a) if a not in o else -encoding.encode(p, a) for a in self.profile.alternatives]]    

def GoalConstraint(scenario, profile, outcome):
    return {
        AnonymousScenario : AnonymousGoal
    }[scenario.__class__](profile, outcome)


###############
#             #
#   DERIVED   #
#             #
###############

class DerivedAxiom(IntraprofileAxiom):

    """Heuristic axiom implied by other axioms."""

    @property
    @abstractmethod
    def activators(self) -> Set[str]:
        """Set of axioms names that imply this axiom."""
        pass
    
    #@final
    def isActive(self, corpus: Set) -> bool:
        """Given a set of axioms, check whether the axioms that imply this axiom are in this set."""
        return self.activators.issubset(set(map(str, corpus)))


class DerivedAxiomInstance(Instance):
    """An instance of a derived axiom."""

    @abstractmethod
    def convertToActivatorsInstances(self) -> Set[Instance]:
        """Convert this instance in a set of instances that imply it."""
        pass


class Symmetry(DerivedAxiom):

    """Derived axiom of Neutrality stating that symmetric alternatives must either all win or all lose."""

    @property
    def activators(self):
        return {"Neutrality"}

    def getInstances(self):
        insts = set()
        for profile in scenario.profiles:
            # This returns the set of instances regarding `profile`
            # (possibly empty).
            insts.update(self.getInstancesMentioning(profile))
        return insts
    
    def getInstancesMentioning(self, profile):

        insts = set()
        
        ballots = list(profile.uniqueBallots())
        profile_dict = profile.as_dict()

        # Get one ballot as reference. We try to match this to other ballots in this profile to construct a self-mapping.
        reference, rest = ballots[0], ballots[1:]

        for ballot in rest:
            # If they can be mapped, they must have the same counter:
            if profile_dict[ballot] == profile_dict[reference]:

                # We try to map this profile into itself by mapping the reference ballot to the current one.
                mapping = {i:j for i, j in zip(reference, ballot)}
                # Construct the new one.
                new_profile_dict = {}
                for b, c in profile_dict.items():
                    new_ballot = (mapping[i] for i in b)
                    new_profile_dict[AnonymousPreference(new_ballot)] = c

                # If we succesfully auto-mapped:
                if new_profile_dict == profile_dict:
                    insts.add(SymmetryInstance(profile, mapping))

        return insts

class SymmetryInstance(DerivedAxiomInstance):

    """Instance of the `Symmetry` derived axiom."""

    def _getClusters(self, mapping):

        """Given a mapping M from alternatives to alternatives expressing an equivalence relation, return the equivalence classes.

        Parameters
        ----------
        mapping : dict
            Dictionary from alternatives to alternatives (int to int). 

        Returns
        -------
        set
            A set of equivalence classes (frozensets) of alternatives.
        """

        # Idea: loop through alternatives and for each of these, traverse
        # the alternatives through the mapping until you loop back to the starting point.
        # This is an equivalence class. Then continue from the next unseen alternative.

        seen = set()
        clusters = set()
        cluster = set()
        for x in mapping:

            # Already in an equivalence class...
            if x in seen:
                continue

            while True:
                # Next alternative.
                y = mapping[x]
                cluster.add(x)
                # If we have looped back,
                if y in cluster:
                    # This is a class.
                    clusters.add(frozenset(cluster))
                    # Set all of these as "already seen".
                    seen.update(cluster)
                    cluster = set()
                    # Let's continue to the next (unseen) alternative.
                    break
                else:
                    # Continue the search.
                    x = y

        return clusters


    def __init__(self, profile, mapping : dict):
        self._profile = profile
        self._mapping = mapping
        # Get the clusters (equivalence classes)
        self._clusters = frozenset(self._getClusters(mapping))

    @property
    def axiom(self):
        return Symmetry

    def mentions(self):
        return {self._profile}

    def as_SAT(self, encoding) -> List[List[int]]:
        cnf = []

        # For each cluster {x1...xj}, we must enforce that: 
        # x1->...->xj->x1 (so if one wins, they all do).

        for cluster in self._clusters:
            first = None
            for x in cluster:
                # If this is the first element of the cluster, do nothing.
                if first is None:
                    first = x
                # Else, add a clause that says that, if the previous alternative of the cluster wins, so must the current one.
                else:
                    cnf.append([-encoding.encode(self._profile, previous), encoding.encode(self._profile, x)])
                # Set the current alternative as the previous one, for the next round.
                previous = x

            # Once we are done, enforce that the last alternative (it is stored in x!) winning implies the first one winning.
            cnf.append([-encoding.encode(self._profile, x), encoding.encode(self._profile, first)])

        return cnf

    def _isEqual(self, other) -> bool:
        return self._profile == other._profile

    def _hashable(self):
        return self._profile, self._clusters

    def convertToActivatorsInstances(self) -> Set:
        # Simply, generate an instance of Neutrality regarding this profile, with this mapping.
        return {NeutralityInstance(self._profile, self._mapping, self._profile)}

    def __str__(self):
        if len(self._clusters) > 1:
            return f"Profile ({self._profile}) is self-connected through neutrality. For each cluster C in {{{', '.join(map(lambda x: str(set(x)), self._clusters))}}}, either all elements of C win or they all lose."
        else:
            return f"Profile ({self._profile}) is self-connected through neutrality. Either all elements of {', '.join(map(lambda x: str(set(x)), self._clusters))} win or they all lose."