from COMSOC.interfaces.axioms import Instance, Axiom, IntraprofileAxiom
from COMSOC.interfaces.model import AbstractProfile

from COMSOC.anonymous.axioms import Neutrality, NeutralityInstance
from COMSOC.anonymous.axioms import Cancellation, CancellationInstance
from COMSOC.anonymous.axioms import PositiveResponsiveness, PositiveResponsivenessInstance

from COMSOC.anonymous.model import AnonymousScenario, AnonymousPreference, AnonymousProfile

from typing import Type, Set, List

from itertools import combinations

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
        return f"In profile ({self._profile}) the outcome should NOT be {self._outcome}."


class AnonymousGoal(AbstractGoalConstraint):

    def as_SAT(self, encoding):
        p, o = self._profile, self._outcome
        return [[encoding.encode(p, a) if a not in o else -encoding.encode(p, a) for a in self.profile.alternatives]]    

    def tree_asp(self):
        """Return the ASP facts, rules and constraints necessary to encode the goal rule."""
        rules = []
        constraints = []

        # Setting priority (Largest for intraprofile axioms)
        #rules.append("priority(2, goal(P,O)) :- instance(goal(P,O)), profile(P), outcome(O).")

        ### Instance might be usable if rule-specific conditions are met
        # Here, usable if target outcome is still possible
        rules.append("localConditionsSatisfied(goal(P,O),N):- profile(P), outcome(O), node(N), statement(N,P,O).")

        ### Description of consequences
        # Using it actually prevents O from being selected for P
        constraints.append(":- step(goal(P,O), N1, N2), instance(goal(P,O)), profile(P), outcome(O), node(N1), node(N2), statement(N2,P,O).")


        ### Forbid side effects
        # Sutor, ne ultra crepidam (wrt outcome O)
        constraints.append(":- step(goal(P,O), N1, N2), instance(goal(P,O)), profile(P), outcome(O), node(N1), node(N2), N1 < N2, statement(N1,P,O1), O1 != O, not statement(N2,P,O1).")

        return [], rules, constraints
    
    def as_asp(self, encoding):
        return [f"goal({encoding.encode_profile(self._profile)},{encoding.encode_outcome(self._outcome)})"]

    def from_asp(self, fact : str, encoding) -> str:
        profile = encoding.encode_profile(self._profile, prettify = True)
        return f"Let us assume, for the sake of contradiction, that {self._outcome} is <i>not</i> the outcome for {profile}."

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
    def activators(self) -> Set[Type[Axiom]]:
        """Set of axioms names that imply this axiom."""
        pass
    
    #@final
    def isActive(self, corpus: Set[Axiom]) -> bool:
        """Given a set of axioms, check whether the axioms that imply this axiom are in this set."""
        return self.activators.issubset(set(map(type, corpus)))


#### Anonymous Voting ####

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
        return {Neutrality}

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

class QuasiTiedWinner(DerivedAxiom):

    @property
    def activators(self):
        return {Cancellation, PositiveResponsiveness}

    def getInstances(self):
        insts = set()
        for profile in scenario.profiles:
            # This returns the set of instances regarding `profile`
            # (possibly empty).
            insts.update(self.getInstancesMentioning(profile))
        return insts

    def _findWinner(self, profile):
        """Given a profile, try to check whether there is a quasi-tied winner.

        A quasi tied winner ties or wins against every other alternative, and wins in at least one case.
        Furthermore, any other pair of alternatives must tie with each other."""

        # Initially, we don't know who the winner is.
        winner = None

        # We try every pair of alternatives.
        for x, y in combinations(profile.alternatives, 2):
            # If we do not know yet who is the winner, if x or y win this contest, then
            # we assume it's the one winning.
            if winner is None:
                contest_winners = profile.majorityContest(x, y)
                if len(contest_winners) < 2:
                    winner = x if x in contest_winners else y
            # If we do know:
            if winner is not None:
                # Every other pair must tie.
                if winner != x and winner != y:
                    contest_winners = profile.majorityContest(x, y)
                    if len(contest_winners) < 2:
                        return None
                # And the winner must tie or win.
                else:
                    loser = (y if winner == x else x)
                    contest_winners = profile.majorityContest(winner, loser)
                    if winner not in contest_winners:
                        return None

        # If we never found a winner, this will be none!
        return winner

    def _tryLoweringAlt(self, ballots, winner, soFar = []):

        """Given a quasi-tied winner, we search recursively for the underlying Cancellation
        profile."""

        # In thise case, we are done: we try to construct the Cancellation profile.
        if not ballots:
            p_dict = {}
            for b in soFar:
                if b in p_dict:
                    p_dict[b] += 1
                else:
                    p_dict[b] = 1

            p = AnonymousProfile(p_dict)
            if p.isPerfectTie():
                return p
            else:
                return None

        # Get the first ballot.
        reference, rest = ballots[0], ballots[1:]

        while True:
            prof = self._tryLoweringAlt(rest, winner, soFar + [reference])
            if prof is not None:
                return prof

            if reference.index(winner) == len(reference) - 1:
                return None
            else:
                reference = list(reference)
                rank = reference.index(winner)
                reference[rank] = reference[rank + 1]
                reference[rank + 1] = winner
                reference = AnonymousPreference(reference)

    def _findCancProfile(self, profile):
        """Find a cancellation profile and a quasi tied winner."""

        winner = self._findWinner(profile)
        if winner is None:
            return None, None
        else:
            return self._tryLoweringAlt(list(profile.allBallots()), winner), winner

    def getInstancesMentioning(self, profile):

        canc_prof, x = self._findCancProfile(profile)
        if canc_prof is not None:
            return {QuasiTiedWinnerInstance(profile, canc_prof, x)}

        return set()
    
class QuasiTiedWinnerInstance(DerivedAxiomInstance):

    """Instance of the `Quasi Tied Winner` derived axiom."""

    def __init__(self, profile, canc_profile, winner):
        self._profile = profile
        self._canc_profile = canc_profile
        self._winner = winner

    @property
    def axiom(self):
        return QuasiTiedWinner

    def mentions(self):
        return {self._profile}

    def as_SAT(self, encoding) -> List[List[int]]:
        return [[(1 if x == self._winner else -1) * encoding.encode(self._profile, x)] for x in self._profile.alternatives]

    def _isEqual(self, other) -> bool:
        return self._profile == other._profile

    def _hashable(self):
        return self._profile

    def convertToActivatorsInstances(self) -> Set:
        return {CancellationInstance(self._canc_profile),\
            PositiveResponsivenessInstance(self._canc_profile, self._winner, self._profile)}

    def __str__(self):
        return f'In profile ({self._profile}), {self._winner} has been raised from ({self._canc_profile}), a Cancellation profile. Thus it must win.'

class QuasiTiedLoser(DerivedAxiom):

    # For the documentation, check the twin axiom QuasiTiedWinner. It is almost equal.

    @property
    def activators(self):
        return {Cancellation, PositiveResponsiveness}

    def getInstances(self):
        insts = set()
        for profile in scenario.profiles:
            # This returns the set of instances regarding `profile`
            # (possibly empty).
            insts.update(self.getInstancesMentioning(profile))
        return insts

    def _findLoser(self, profile):
        loser = None

        for x, y in combinations(profile.alternatives, 2):
            if loser is None:
                contest_winners = profile.majorityContest(x, y)
                if len(contest_winners) < 2:
                    loser = x if y in contest_winners else y
            if loser is not None:
                if loser != x and loser != y:
                    contest_winners = profile.majorityContest(x, y)
                    if len(contest_winners) < 2:
                        return None
                else:
                    winner = (y if loser == x else x)
                    contest_winners = profile.majorityContest(winner, loser)
                    if winner not in contest_winners:
                        return None

        return loser

    def _tryRisingAlt(self, ballots, loser, soFar = []):
        if not ballots:
            p_dict = {}
            for b in soFar:
                if b in p_dict:
                    p_dict[b] += 1
                else:
                    p_dict[b] = 1

            p = AnonymousProfile(p_dict)
            if p.isPerfectTie():
                return p
            else:
                return None

        reference, rest = ballots[0], ballots[1:]

        while True:
            prof = self._tryRisingAlt(rest, loser, soFar + [reference])
            if prof is not None:
                return prof

            if reference.index(loser) == 0:
                return None
            else:
                reference = list(reference)
                rank = reference.index(loser)
                reference[rank] = reference[rank - 1]
                reference[rank - 1] = loser
                reference = AnonymousPreference(reference)

    def _findCancProfile(self, profile):
        loser = self._findLoser(profile)
        if loser is None:
            return None, None
        else:
            return self._tryRisingAlt(list(profile.allBallots()), loser), loser

    def getInstancesMentioning(self, profile):

        canc_prof, x = self._findCancProfile(profile)
        if canc_prof is not None:
            return {QuasiTiedLoserInstance(profile, canc_prof, x)}

        return set()
    
class QuasiTiedLoserInstance(DerivedAxiomInstance):

    """Instance of the `Quasi Tied Loser` derived axiom."""

    def __init__(self, profile, canc_profile, loser):
        self._profile = profile
        self._canc_profile = canc_profile
        self._loser = loser

    @property
    def axiom(self):
        return QuasiTiedLoser

    def mentions(self):
        return {self._profile}

    def as_SAT(self, encoding) -> List[List[int]]:
        return [[-encoding.encode(self._profile, self._loser)]]

    def _isEqual(self, other) -> bool:
        return self._profile == other._profile

    def _hashable(self):
        return self._profile

    def convertToActivatorsInstances(self) -> Set:
        return {CancellationInstance(self._canc_profile),\
            PositiveResponsivenessInstance(self._profile, self._loser, self._canc_profile)}

    def __str__(self):
        return f'In profile ({self._profile}), {self._loser} has been lowered from ({self._canc_prof}), a Cancellation profile. Thus it cannot win here.'