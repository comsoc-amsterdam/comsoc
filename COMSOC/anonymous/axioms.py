from COMSOC.interfaces.axioms import Axiom, IntraprofileAxiom, InterprofileAxiom, Instance
import COMSOC.anonymous.model as model

from typing import List, Set, Type
from itertools import permutations, combinations

from COMSOC.helpers import powerset

import re

########### INTRAPROFILE AXIOMS ################

class AtLeastOne(IntraprofileAxiom):

    """Axiom encoding the fact that, for every profile, at least one alternative must win."""

    def getInstances(self) -> Set:
        return {AtLeastOneInstance(profile) for profile in self.scenario.profiles}

    def getInstancesMentioning(self, profile) -> Set:
        return {AtLeastOneInstance(profile)}

    def tree_asp(self):
        """Return facts, rules, constraints for building the ASP tree."""
        # Nothing.
        return [], [], []

class AtLeastOneInstance(Instance):

    """Instance of the `At Least One` axiom."""

    def __init__(self, profile):
        self._profile = profile

    @property    
    def axiom(self) -> Type[Axiom]:
        return AtLeastOne

    def mentions(self):
        return {self._profile}

    def as_SAT(self, encoding) -> List[List[int]]:
        # Return a CNF with a single clause stating that at least one alternative must win
        return [[encoding.encode(self._profile, x) for x in self._profile.alternatives]]

    def as_asp(self, encoding):
        # Not used
        #return [f"atleastone({encoding.encode_profile(self._profile)})"]
        return []

    def from_asp(self, fact : str, encoding, prettify = False) -> str:
        # Not used.
        return ""

    def _isEqual(self, other) -> bool:
        return self._profile == other._profile

    def _hashable(self):
        return self._profile

    def __str__(self):
        return f"In profile ({self._profile}) at least one alternative must win."

class Faithfulness(IntraprofileAxiom):

    """Axiom encoding the fact that, if there is only one voter, her top-ranked alternative must be the unique winner."""

    def getInstances(self) -> Set:
        return {FaithfulnessInstance(profile) for profile in self.scenario.profilesOfSize(1)}

    def getInstancesMentioning(self, profile) -> Set:
        return {FaithfulnessInstance(profile)} if len(profile) == 1 else set()

    def tree_asp(self):
        """Return the ASP facts, rules and constraints necessary to encode the Faithfulness rule."""
        rules = []
        constraints = []

        # Setting priority (Largest for intraprofile axioms)
        #rules.append("priority(2, faithfulness(P,O)) :- instance(faithfulness(P,O)), profile(P), outcome(O).")

        ### Instance might be usable if rule-specific conditions are met
        # Here, usable if O is not already the finale outcome for P
        rules.append("localConditionsSatisfied(faithfulness(P,O),N):- profile(P), outcome(O), node(N), not finaleOutcome(N,P,O).")


        ### Description of consequences
        # Using it actually prevents any outcome different from O to be possible for P if O was possible
        constraints.append(":- step(faithfulness(P,O), N1, N2), instance(faithfulness(P,O)), profile(P), outcome(O), node(N1), node(N2), N1 < N2, statement(N1,P,O), statement(N2,P,O1), outcome(O1), O1 != O.")

        # Otherwise, if O was not possible, we reach a contradiction and (P,oEmpty) is the only statement in N2 for P
        constraints.append(":- step(faithfulness(P,O), N1, N2), instance(faithfulness(P,O)), profile(P), outcome(O), node(N1), node(N2), N1 < N2, not statement(N1,P,O), not statement(N2,P,oEmpty).")


        return [], rules, constraints

class FaithfulnessInstance(Instance):

    """Instance of the Faitfhulness Axiom."""

    def __init__(self, profile):
        self._profile = profile
        self._winner = profile.top()

    @property
    def axiom(self) -> Type[Axiom]:
        return Faithfulness

    def mentions(self):
        return {self._profile}

    def _isEqual(self, other) -> bool:
        return self._profile == other._profile

    def _hashable(self):
        return self._profile

    def as_SAT(self, encoding) -> List[List[int]]:
        # The CNF is made of singleton clauses. For every alternative, we have one clause stating that it must win 
        # (if it is the top ranked one) or lose (otherwise)
        return [[(1 if x == self._winner else -1) * encoding.encode(self._profile, x)] for x in self._profile.alternatives]

    def as_asp(self, encoding):
        outcome = model.AnonymousOutcome({self._winner})
        return [f"faithfulness({encoding.encode_profile(self._profile)},{encoding.encode_outcome(outcome)})"]

    def from_asp(self, fact : str, encoding, prettify = False) -> str:
        profile = encoding.encode_profile(self._profile, prettify = prettify)
        if prettify:
            return f"Since {profile} has only one voter, by Faithfulness, her favourite alternative, <i>{self._winner}</i>, should be the unique winner."
        else:
            return f"Since {profile} has only one voter, by Faithfulness, her favourite alternative, {self._winner}, should be the unique winner."

    def __str__(self):
        return f"In profile ({self._profile}) there is only one voter. Hence, their favourite alternative should win."

class Pareto(IntraprofileAxiom):

    """Axiom encoding the fact that no dominated alternative can win."""

    def getInstances(self) -> Set:
        insts = set()
        for profile in self.scenario.profiles:
            # This returns the set of instances regarding `profile`
            # (possibly empty).
            insts.update(self.getInstancesMentioning(profile))
        return insts

    def getInstancesMentioning(self, profile) -> Set:
        # Generate 1 instance for every pareto-dom alternative x.
        insts = set()
        for x in profile.alternatives:
            if profile.isParetoDom(x):
                insts.add(ParetoInstance(profile, x))
        return insts

    def tree_asp(self):
        """Return the ASP facts, rules and constraints necessary to encode the Pareto rule."""
        rules = []
        constraints = []

        # Setting priority (Largest for intraprofile axioms)
        #rules.append("priority(3, pareto(P,Y)) :- instance(pareto(P,Y)), profile(P1), alternative(Y).")

        ### Instance might be usable if rule-specific conditions are met
        # Here, usable if P has at least one possible outcome containing Y
        rules.append("localConditionsSatisfied(pareto(P,Y),N):- profile(P), alternative(Y), node(N), statement(N,P,O), outcome(O), inOutcome(Y,O).")

        ### Description of consequences
        # Using it actually prevents Y from being in the outcome
        constraints.append(":- step(pareto(P,Y), N1, N2), instance(pareto(P,Y)), profile(P), alternative(Y), node(N1), node(N2), N1 < N2, statement(N2,P,O), outcome(O), inOutcome(Y,O).")

        ### Forbid side effects
        # Sutor, ne ultra crepidam (wrt alternative Y)
        constraints.append(":- step(pareto(P,Y), N1, N2), instance(pareto(P,Y)), profile(P), alternative(Y), node(N1), node(N2), N1 < N2, statement(N1,P,O), not inOutcome(Y,O), not statement(N2,P,O).")

        return [], rules, constraints

class ParetoInstance(Instance):

    """Instance of the `Pareto Principle` axiom."""

    def __init__(self, profile, dominated):
        self._profile = profile
        self._dominated = dominated

    @property
    def axiom(self) -> Type[Axiom]:
        return Pareto

    def mentions(self):
        return {self._profile}

    def _isEqual(self, other) -> bool:
        return self._profile == other._profile and self._dominated == other._dominated

    def _hashable(self):
        return self._profile, self._dominated

    def as_SAT(self, encoding) -> List[List[int]]:
        # The pareto dominated alternative cannot win.
        return [[-encoding.encode(self._profile, self._dominated)]]

    def as_asp(self, encoding):
        return [f"pareto({encoding.encode_profile(self._profile)},{encoding.encode_alternative(self._dominated)})"]

    def from_asp(self, fact : str, encoding, prettify = False) -> str:
        profile = encoding.encode_profile(self._profile, prettify = prettify)
        if prettify:
            return f"In profile {profile}, alternative <i>{self._dominated}</i> is Pareto-dominated. Hence, it cannot be among the winners."
        else:
            return f"In profile {profile}, alternative {self._dominated} is Pareto-dominated. Hence, it cannot be among the winners."

    def __str__(self):
        return f"In profile ({self._profile}) alternative {self._dominated} is Pareto-dominated. Hence, it cannot win."        

class Cancellation(IntraprofileAxiom):

    """Axiom encoding the fact that, if all alternatives tie in majority contests, all alternatives win."""

    def getInstances(self) -> Set:
        return {CancellationInstance(profile) for profile in self.scenario.profiles if profile.isPerfectTie()}

    def getInstancesMentioning(self, profile) -> Set:
        return {CancellationInstance(profile)} if profile.isPerfectTie() else set()

    def tree_asp(self):
        """Return the ASP facts, rules and constraints necessary to encode the Cancellation rule."""
        facts = []
        rules = []
        constraints = []

        # Setting priority (Largest for intraprofile axioms)
        #rules.append("priority(2, cancellation(P)) :- instance(cancellation(P)), profile(P), outcome(O).")

        ### Instance might be usable if rule-specific conditions are met
        # Here, usable if fullOutcome is not already the finale outcome for P
        rules.append("localConditionsSatisfied(cancellation(P,O),N):- profile(P), fullOutcome(O), node(N), not finaleOutcome(N,P,O).")

        ### Description of consequences
        # Using it actually prevents any outcome different from fullOutcome to be possible for P if fullOutcome was possible
        constraints.append(":- step(cancellation(P,O), N1, N2), instance(cancellation(P,O)), profile(P), node(N1), node(N2), N1 < N2, fullOutcome(O), statement(N1,P,O), statement(N2,P,O1), outcome(O1), O != O1.")

        # Otherwise, if fullOutcome was not possible, we reach a contradiction and (P,oEmpty) is the only statement in N2 for P
        constraints.append(":- step(cancellation(P,O), N1, N2), instance(cancellation(P,O)), profile(P), fullOutcome(O), node(N1), node(N2), N1 < N2, not statement(N1,P,O), not statement(N2,P,oEmpty).")

        return facts, rules, constraints

class CancellationInstance(Instance):

    """Instance of the `Cancellation` axiom."""

    def __init__(self, profile):
        self._profile = profile

    @property
    def axiom(self) -> Type[Axiom]:
        return Cancellation

    def mentions(self):
        return {self._profile}

    def _isEqual(self, other) -> bool:
        return self._profile == other._profile

    def _hashable(self):
        return self._profile

    def as_SAT(self, encoding) -> List[List[int]]:
        # All alternatives win (one clause per alternative).
        return [[encoding.encode(self._profile, x)] for x in self._profile.alternatives]

    def as_asp(self, encoding):
        full_outcome = encoding.encode_outcome(model.AnonymousOutcome(self._profile.alternatives))
        return [f"cancellation({encoding.encode_profile(self._profile)},{full_outcome})"]

    def from_asp(self, fact : str, encoding, prettify = False) -> str:
        return f"Profile {encoding.encode_profile(self._profile, prettify = prettify)} is a perfect tie: by Cancellation, all alternatives must win here."

    def __str__(self):
        return f"Profile ({self._profile}) is a perfect tie: all alternatives must win here."

class Condorcet(IntraprofileAxiom):

    """Axiom encoding the fact that, if a Condorcet winner exists, it must win."""

    def getInstances(self) -> Set:
        return {CondorcetInstance(profile) for profile in self.scenario.profiles if profile.hasCondorcetWinner()}

    def getInstancesMentioning(self, profile) -> Set:
        return {CondorcetInstance(profile)} if profile.hasCondorcetWinner() else set()

    def tree_asp(self):
        """Return the ASP facts, rules and constraints necessary to encode the Condorcet rule."""
        rules = []
        constraints = []


        ### Instance might be usable if rule-specific conditions are met
        # Here, usable if O is not already the finale outcome for P
        rules.append("localConditionsSatisfied(condorcet(P,O),N):- profile(P), outcome(O), node(N), not finaleOutcome(N,P,O).")


        ### Description of consequences
        # Using it actually prevents any outcome different from O to be possible for P if O was possible
        constraints.append(":- step(condorcet(P,O), N1, N2), instance(condorcet(P,O)), profile(P), outcome(O), node(N1), node(N2), N1 < N2, statement(N1,P,O), statement(N2,P,O1), outcome(O1), O1 != O.")

        # Otherwise, if O was not possible, we reach a contradiction and (P,oEmpty) is the only statement in N2 for P
        constraints.append(":- step(condorcet(P,O), N1, N2), instance(condorcet(P,O)), profile(P), outcome(O), node(N1), node(N2), N1 < N2, not statement(N1,P,O), not statement(N2,P,oEmpty).")

        return [], rules, constraints

class CondorcetInstance(Instance):

    """Instance of the `Condorcet` axiom."""

    def __init__(self, profile):
        self._profile = profile
        self._winner = profile.condorcetWinner()

    @property
    def axiom(self) -> Type[Axiom]:
        return Condorcet

    def mentions(self):
        return {self._profile}

    def _isEqual(self, other) -> bool:
        return self._profile == other._profile

    def _hashable(self):
        return self._profile

    def as_SAT(self, encoding) -> List[List[int]]:
        # Only the Condorcet winner wins.
        return [[(1 if x == self._winner else -1) * encoding.encode(self._profile, x)] for x in self._profile.alternatives]

    def as_asp(self, encoding):
        outcome = encoding.encode_outcome(model.AnonymousOutcome({self._winner}))
        return [f"condorcet({encoding.encode_profile(self._profile)},{outcome})"]

    def from_asp(self, fact : str, encoding, prettify = False) -> str:
        profile = encoding.encode_profile(self._profile, prettify = prettify)
        if prettify:
            return f"Alternative <i>{self._winner}</i> is the Condorcet winner of profile {profile}. Hence, it must be the unique winner."
        else:
            return f"Alternative {self._winner} is the Condorcet winner of profile {profile}. Hence, it must be the unique winner."

    def __str__(self):
        return f"Alternative {self._winner} is the Condorcet winner of profile {self._profile}. Hence, it must be the unique winner."

########### INTERPROFILE AXIOMS ################

class Neutrality(InterprofileAxiom):

    """Axiom encoding the fact that all alternatives must be treated equally."""

    def _getMappingIfPermutable(self, profile1, profile2):

        """If there exists a mapping of alternatives M so that M(p) = q, return it. Otherwise, return None."""

        # Get ANY pair (ballot, count) from profile1.
        # We will use this ballot as a reference to construct the candidate mappings.
        for reference_ballot, reference_count in profile1.ballotsWithCounts():
            break

        p2dict = profile2.as_dict()

        # For every ballot, count of profile2:
        for ballot, count in p2dict.items():
            # If the count of this ballot matches the count of our reference ballot,
            if count == reference_count:
                # Construct the mapping from our reference to this ballot.
                candidate_mapping = {i:j for i, j in zip(reference_ballot, ballot)}

                # Now, construct the resulting dictionary by applying this mapping to all
                # ballots of profile2.
                new_profile_dict = {}
                for ballot2, count2 in profile1.ballotsWithCounts():
                    new_profile_dict[model.AnonymousPreference(candidate_mapping[b] for b in ballot2)] = count2

                # If this new dictionary is equal to the dictionary of profile2, return this one.
                if new_profile_dict == p2dict:
                    return candidate_mapping

        # Nothing found.
        return None

    def getInstances(self):
        insts = set()

        # For all possible sizes of profiles:
        for size in range(1, self.scenario.nVoters+1):
            # For all two unordered pairs of profiles of this size,
            for p, q in combinations(self.scenario.profilesOfSize(size), 2):
                # if it exists, construct the mapping, and make the corresponding instance.
                # IMPORTANT! We are not generating the inverse, but this is fine, because we consider the two equal
                # (the inverse is from q to p). Check __equal__() to see that indeed they are equal!
                mapping = self._getMappingIfPermutable(p, q)
                if mapping is not None:
                    insts.add(NeutralityInstance(p, mapping, q))
        return insts

    def getInstancesMentioning(self, profile):
        ballot = profile.anyBallot()
        result = set()
        # Generate all permutations of a ballot:
        for perm in permutations(ballot):
            if ballot != perm:
                # Construct the corresponding mapping.
                mapping = {b:c for b, c in zip(ballot, perm)}
                # With it, construct the new profile.
                new_profile_dict = {}
                for bballot, count in profile.ballotsWithCounts():
                    new_profile_dict[model.AnonymousPreference(mapping[b] for b in bballot)] = count
                new_profile = model.AnonymousProfile(new_profile_dict)

                # Add the corresponding instance.
                result.add(NeutralityInstance(profile, mapping, new_profile))

        return result

    def getInstancesMentioningHeuristic(self, profile, heur_info):
        # If this is already connected by neutrality, we have no need to generate new instances.
        if not heur_info["reachedByNeutrality"]:
            return self.getInstancesMentioning(profile)
        else:
            return set()

    def tree_asp(self):
        """Return the ASP facts, rules and constraints necessary to encode the Neutrality rule."""
        facts = []
        rules = []
        constraints = []

        # Setting priority (Second largest for interprofile axioms)
        #rules.append("priority(2, neutrality(P1,O1,P2,O2)) :- instance(neutrality(P1,O1,P2,O2)), profile(P1), outcome(O1),  profile(P2), outcome(O2).")

        ### Instance might be usable if rule-specific conditions are met
        # Here, usable at any time (merging possible outcomes for both profiles wrt perm on alternatives)
        rules.append("localConditionsSatisfied(neutrality(P1,O1,P2,O2),N):- profile(P1), outcome(O1), profile(P2), outcome(O2), node(N).")


        ### Description of consequences

        # Rule can be used if P1 and P2 have been introduced, O1 is possible for P1 or O2 is possible for P2 but not both of them are finale
        rules.append("canBeUsed(neutrality(P1,O1,P2,O2), N) :- instance(neutrality(P1,O1,P2,O2)), profile(P1), profile(P2), outcome(O1), outcome(O2), node(N), not leaf(N), isIntroduced(P1,N), isIntroduced(P2,N), 1 {statement(N,P1,O1) ; statement(N,P2,O2)}, not 2 {finaleOutcome(N,P1,O1) ; finaleOutcome(N,P2,O2)} 2.")

        # If an instance speaks of only one profile, then, if O1 and O2 are different, none of them can be the real outcome
        constraints.append(":- step(neutrality(P,O1,P,O2), N1, N2), instance(neutrality(P,O1,P,O2)), profile(P), outcome(O1), outcome(O2), O1 != O2, N1 < N2, 1{statement(N2,P,O1); statement(N2,P,O2)}.")
        # If an instance speaks of only one profile, then, equal outcomes are ok
        constraints.append(":- step(neutrality(P,O,P,O), N1, N2), instance(neutrality(P,O,P,O)), profile(P), outcome(O), N1 < N2, statement(N1,P,O), not statement(N2,P,O).")

        # If O1 is a possible outcome for P1 and O2 is a possible outcome for P2, O1 still a possible outcome for P1
        constraints.append(":- step(neutrality(P1,O1,P2,O2), N1, N2), instance(neutrality(P1,O1,P2,O2)), profile(P1), outcome(O1), profile(P2), outcome(O2), node(N1), node(N2), N1 < N2, statement(N1,P1,O1), statement(N1,P2,O2), not statement(N2,P1,O1), P1 != P2.")
        # If O1 is a possible outcome for P1 and O2 is a possible outcome for P2, O2 still a possible outcome for P2
        constraints.append(":- step(neutrality(P1,O1,P2,O2), N1, N2), instance(neutrality(P1,O1,P2,O2)), profile(P1), outcome(O1), profile(P2), outcome(O2), node(N1), node(N2), N1 < N2, statement(N1,P1,O1), statement(N1,P2,O2), not statement(N2,P2,O2), P1 != P2.")

        # If O1 was possible for P1 but O2 was not for P2, then O1 it's not possible for P1 anymore
        constraints.append(":-  step(neutrality(P1,O1,P2,O2), N1, N2), instance(neutrality(P1,O1,P2,O2)), profile(P1), outcome(O1), profile(P2), outcome(O2),  node(N1), node(N2), N1 < N2, statement(N1,P1,O1), not statement(N1,P2,O2), statement(N2,P1,O1), P1 != P2.")
        # If O1 was possible for P1 but O2 was not for P2, then O2 is still not possible for P2
        constraints.append(":-  step(neutrality(P1,O1,P2,O2), N1, N2), instance(neutrality(P1,O1,P2,O2)), profile(P1), outcome(O1), profile(P2), outcome(O2), node(N1), node(N2), N1 < N2, statement(N1,P1,O1), not statement(N1,P2,O2), statement(N2,P2,O2), outcome(O), P1 != P2.")

        # If O2 was possible for P2 but O1 was not for P1, then O1 still not possible for P1
        constraints.append(":-  step(neutrality(P1,O1,P2,O2), N1, N2), instance(neutrality(P1,O1,P2,O2)), profile(P1), outcome(O1), profile(P2), outcome(O2),  node(N1), node(N2), N1 < N2, statement(N1,P2,O2), not statement(N1,P1,O1), statement(N2,P1,O1), outcome(O), P1 != P2.")
        # If O2 was possible for P2 but O1 was not for P1, then O2 is not possible for P2 anymore
        constraints.append(":-  step(neutrality(P1,O1,P2,O2), N1, N2), instance(neutrality(P1,O1,P2,O2)), profile(P1), outcome(O1), profile(P2), outcome(O2),  node(N1), node(N2), N1 < N2, statement(N1,P2,O2), not statement(N1,P1,O1), statement(N2,P2,O2), outcome(O), P1 != P2.")


        # Sutor, ne ultra crepidam (wrt to O1 for P1)
        constraints.append(":- step(neutrality(P1,O1,P2,O2), N1, N2), instance(neutrality(P1,O1,P2,O2)), profile(P1), outcome(O1), profile(P2), outcome(O2),  node(N1), node(N2), N1 < N2, statement(N1,P1,O), outcome(O), O1 != O, not statement(N2,P1,O), P1 != P2.")

        # Sutor, ne ultra crepidam (wrt to O2 for P2)
        constraints.append(":- step(neutrality(P1,O1,P2,O2), N1, N2), instance(neutrality(P1,O1,P2,O2)), profile(P1), outcome(O1), profile(P2), outcome(O2),  node(N1), node(N2), N1 < N2, statement(N1,P2,O), outcome(O), O2 != O, not statement(N2,P2,O), P1 != P2.")

        # Sutor, ne ultra crepidam (wrt a single profile and O1 and O2)
        constraints.append(":- step(neutrality(P,O1,P,O2), N1, N2), instance(neutrality(P,O1,P,O2)), profile(P), outcome(O1), outcome(O2),  node(N1), node(N2), N1 < N2, statement(N1,P,O), outcome(O), O2 != O, O1 != O, not statement(N2,P,O).")


        # LEMMAS! 
            
        # Lemma.
        # If no outcome O possible for P, st neut(P,O,P,O) => close branch

        ### Instance might be usable if rule-specific conditions are met
        # Here, usable if P doesn't have any possible outcome O left st neut(P,O,P,O) is in the explanation
        rules.append("localConditionsSatisfied(lemmaNeu(P),N):- profile(P), instance(lemmaNeu(P)), node(N), #count {O : outcome(O), statement(N,P,O), instance(neutrality(P,O,P,O))} == 0.")

        ### Description of consequences
        # Using it closes the branch (no more possible outcomes for P1)
        constraints.append(":- step(lemmaNeu(P), N1, N2), instance(lemmaNeu(P)), profile(P), node(N1), node(N2), N1 < N2, not statement(N2,P,oEmpty).")

        ## Lemma 2

        # Lemma.
        # If only a single outcome O is possible for p, st neu(p,O,p,O) => assign O to p

        ### Instance might be usable if rule-specific conditions are met
        # Here, usable if P has a single possible outcome O st neut(P1,O,P2,O) is in the explanation
        rules.append("localConditionsSatisfied(lemmaNeuV2(P,O),N):- profile(P), instance(lemmaNeuV2(P,O)), node(N), outcome(O), statement(N,P,O), instance(neutrality(P,O,P,O)), #count {outcome(O1) : statement(N,P,O1), instance(neutrality(P,O1,P,O1))} == 1.")

        ### Description of consequences
        # Using it assigns O to both profiles as a final outcome
        rules.append("""onlyPossible(O,P,N) :- outcome(O), profile(P), node(N), statement(N,P,O),
                        instance(neutrality(P,O,P,O)), #count {O1 : outcome(O1), statement(N,P,O1),
                        instance(neutrality(P,O1,P,O1))} == 1.""")

        constraints.append(":- step(lemmaNeuV2(P,O), N1, N2), instance(lemmaNeuV2(P,O)), profile(P), node(N1), node(N2), N1 < N2, outcome(O), onlyPossible(O,P,N1), statement(N2,P,O1), outcome(O1), O1 != O.")

        return facts, rules, constraints

class NeutralityInstance(Instance):

    """Instance of the `Cancellation` axiom."""

    class HashableDict(dict):

        """Private class that represents a hashable dictionary. Used to hash this instance, since a mapping is a dictionary."""

        def __init__(self, data: dict):
            dict.__init__(self, data)
            self._key = frozenset(frozenset((a, b)) for a, b in data.items())

        def __hash__(self):
            return hash(self._key)

        def __eq__(self, other):
            return self._key == other._key

        def __str__(self):
            return '{' + ', '.join(f'{x}~{y}' for x, y in self.items()) + '}'

    def __init__(self, base, mapping: dict, mapped):
        self._base = base
        # We want it to be hashable, because the instance needs to be hashable; and the hashable
        # needs to be consistent with the __equal__ function, which looks at the mapping. This is because
        # there can be different ways to map two profiles, and hence, different instances betweem two profiles.
        self._mapping = self.HashableDict(mapping)
        self._mapped = mapped
        self._profiles = frozenset((self._base, self._mapped))

    @property
    def axiom(self) -> Type[Axiom]:
        return Neutrality

    def mentions(self):
        return self._profiles

    def _isEqual(self, other) -> bool:
        return self._profile == other._profile

    def _hashable(self):
        return self._profile

    def as_SAT(self, encoding):
        # if x wins in the base profile, mapping(x) must win in mapping(base)
        # and vice versa
        cnf = []
        for x, mapped_x in self._mapping.items():
            cnf.append([-encoding.encode(self._base, x), encoding.encode(self._mapped, mapped_x)])
            cnf.append([encoding.encode(self._base, x), -encoding.encode(self._mapped, mapped_x)])

        return cnf

    def as_asp(self, encoding):

        asp = []

        base = encoding.encode_profile(self._base)
        mapped = encoding.encode_profile(self._mapped)

        for outcome in map(model.AnonymousOutcome, powerset(self._base.alternatives)):
            if outcome:

                encoded_outcome = encoding.encode_outcome(outcome)

                mapped_outcome = model.AnonymousOutcome(self._mapping[a] for a in outcome)
                encoded_mapped_outcome = encoding.encode_outcome(mapped_outcome)
                
                asp.append(f"neutrality({base},{encoded_outcome},{mapped},{encoded_mapped_outcome})")

                if len(self._profiles) == 1:  # use lemmas
                    asp.append(f"lemmaNeuV2({base},{encoded_outcome})")

        if len(self._profiles) == 1:  # use lemmas
            asp.append(f"lemmaNeu({base})")
                    


        
        return asp

    def from_asp(self, fact: str, encoding, prettify = False) -> str:

        profiles = list(map(lambda x: encoding.encode_profile(x, prettify = prettify), self._profiles))

        if 'lemmaNeu' in fact:
            if 'V2' in fact:
                outcome = list(map(encoding.decode, re.findall('o[^,\)]+', fact)))[0]
                if prettify:
                    outcome = outcome.prettify()
                return f"Outcome {outcome} is the only available outcome for {profiles[0]} that would not contradict Neutrality. Indeed, if any alternative in {outcome} would lose, that would be an unfair treatment, since it is symmetrical to the others."
            else:
                return f"Every outcome available for {profiles[0]} would contradict Neutrality."

        outcomes = list(map(encoding.decode, re.findall('o[^,\)]+', fact)))

        if len(set(profiles)) == 1:  # only one profile involved.
            if len(outcomes[0]) == 1 and len(outcomes[1]) == 1:
                if prettify:
                    return f"If <i>{list(outcomes[0])[0]}</i> was the unique winner for {profiles[0]}, then we would contradict Neutrality, as it should be treated equally to <i>{list(outcomes[1])[0]}</i> (and vice versa). Hence, neither can be the unique winners."
                else:
                    return f"If {list(outcomes[0])[0]} was the unique winner for {profiles[0]}, then we would contradict Neutrality, as it should be treated equally to {list(outcomes[1])[0]} (and vice versa). Hence, neither can be the unique winners."
            else:
                if prettify:
                    return f"If {outcomes[0].prettify()} were to be the (tied) winners for {profiles[0]}, then we would contradict Neutrality, as these alternatives should be treated equally to {outcomes[1].prettify()} (and vice versa). Hence, neither set can be the outcome."
                else:
                    return f"If {outcomes[0]} were to be the (tied) winners for {profiles[0]}, then we would contradict Neutrality, as these alternatives should be treated equally to {outcomes[1]} (and vice versa). Hence, neither set can be the outcome."
        else:
            return f"By Neutrality, if {outcomes[0].prettify() if prettify else outcomes[0]} is the outcome for {profiles[0]}, then {outcomes[1].prettify() if prettify else outcomes[0]} must be the outcome of {profiles[1]} (or vice versa)."

    def _isEqual(self, other):
        return self._profiles == other._profiles and self._mapping == other._mapping

    def _hashable(self):
        return self._profiles, self._mapping

    def __str__(self):
        return f"Profiles ({self._base}) and ({self._mapped}) are identical up to a renaming of the alternatives: {self._mapping}. Hence, the outcomes must be equal under the same renaming."

class PositiveResponsiveness(InterprofileAxiom):

    """Axiom encoding the fact that if a (possibly tied) alternative receives increased support, then it must be the unique winner."""

    def _remove_alt_data(self, profile, x):
        """Clean a profile from an alternative.

        Will return two dictionaries: one mapping every cleaned ballot B to the list
        of ballots that, if we remove x from it, we obtain B.
        One mapping every cleaned ballot B to the total number of voters whose cleaned
        ballot is B."""
        counts, ballots = {}, {}
        for ballot, count in profile.ballotsWithCounts():
            # Remove x.
            cleaned = model.AnonymousPreference(y for y in ballot if x != y)

            if not cleaned in ballots:
                ballots[cleaned] = []
            ballots[cleaned].extend([ballot] * count)

            if not cleaned in counts:
                counts[cleaned] = 0
            counts[cleaned] += count

        return counts, ballots        

    def _check_profs(self, p, q):
        """Check whether between two profiles there are instances of Positive Responsiveness.

        For each instance that exists between p and q,
        return a tuple of form (base, raised, x). Here, `base` is a profile (p or q) such that,
        by raising the support of x, we obtain `raised` (again, p or q). We return a list of such
        tuples."""

        results = []

        # The two profiles must be distinct.
        if p != q:
            # Let us try all alternatives, and see if, for one of them,
            # we find an instance.
            for x in self.scenario.alternatives:
                # This function removes "x" from the alternatives of these profiles;
                # p_ballots maps each "cleaned" ballot B to a set of ballots B' of p such that,
                # by removing x from B', we obtain B. p_counts counts for every cleaned ballot B
                # the *total* number of voters such that, if you remove x from their ballot, you
                # obtain B.
                p_counts, p_ballots = self._remove_alt_data(p, x)
                q_counts, q_ballots = self._remove_alt_data(q, x)
                # To be an instance of PosRes, everything else besides x must be
                # equal.
                if p_counts == q_counts:
                    # Now, we have to do the following. For every cleaned ballot B,
                    # the sets of ballots in p_ballots[B] and q_ballots[B] only differ in 
                    # where x is ranked. We need to pair every ballot in p_ballots[B]
                    # to a ballot in q_ballots[B] such that the rank of x 
                    # is the same or has been increased for one of the two (and the direction
                    # of the increase must always be the same, i.e., always p or always q).
                    # If we can do this for every cleaned ballot B, then we we succeeded.

                    # Initially, we don't know if p is the profile where the support
                    # of x has increased or if q is.
                    direction = 'unk'

                    # Hence, for every set of cleaned ballot (note that these are equal for p and q)...
                    for ballot in p_ballots:

                        # To make the pairings, we keep the ballots from p fixed,
                        # and try every permutations of the ballots from q.

                        # Recall that, given a cleaned ballot B, p_ballots[B] contains
                        # the list of ballots such that, if you remove x, you get B.
                        p_list = p_ballots[ballot]  # this is a list.
                        for q_list in permutations(q_ballots[ballot]):

                            # This will be explained later...
                            failed = False
                            direction_old = direction

                            # We pair each ballots (recall that we try every permutation of q_list)
                            for p_ballot, q_ballot in zip(p_list, q_list):
                                # We don't know yet, so we check.
                                if direction == 'unk':
                                    # If the rank of x is lower in p than in q,
                                    # then the support of x has increased in p from q.
                                    if p_ballot.rank(x) < q_ballot.rank(x):
                                        direction = 'p raises q'
                                    # Other direction
                                    elif p_ballot.rank(x) > q_ballot.rank(x):
                                        direction = 'q raises p'
                                    # Else, we can't say anything. Still `unk`.
                                # If we do know something,
                                else:
                                    # If the rank in p is greater AND this contradicts
                                    # what we have seen so far, we have failed.
                                    if p_ballot.rank(x) > q_ballot.rank(x) and\
                                        direction == 'p raises q':
                                            failed = True
                                            break
                                    if p_ballot.rank(x) < q_ballot.rank(x) and\
                                        direction == 'q raises p':
                                            failed = True
                                            break

                            # If we failed, we reset direction to direction_old, i.e., before
                            # trying the mapping;
                            # this means that, if we were in state `unk` before trying this mapping,
                            # we are still in that state.
                            if failed:
                                direction = direction_old
                            # If we did not fail, this mapping works; hence we break, and return to the outer
                            # loop.
                            if not failed:
                                break

                        # If this is the case, it means we tried every mapping, and
                        # failed all of them (otherwise, we would have breaked without failure
                        # before). Hence we break out from this loop as well, there is no
                        # use in trying out the next ballot.
                        if failed:
                            break

                    # If we got to here without every failing,
                    # then we do know the direction, and can create
                    # the result accordingly.
                    if direction == 'p raises q':
                        results.append((q, p, x))
                    elif direction == 'q raises p':
                        results.append((p, q, x))

        return results

    def getInstances(self):
        insts = set()
        # Of course, if we only have one alternative, there are no instances (no increase possible)
        if len(self.scenario.alternatives) > 1:
            # Then, for every possible size of profiles.
            for size in range(1, self.scenario.nVoters+1):
                # We get all (unordered) pairs of profiles of the same size
                # (we can have an instance only between profiles of the same size).
                for p, q in combinations(self.scenario.profilesOfSize(size), 2):
                    # If there is an instance between p and q, this will return a tuple
                    # (base, raised, x), where the support of x in base has been augmented
                    # to obtan raised. Otherwise, returns None.
                    for base, raised, x in self._check_profs(p, q):
                        # If we found an instance, create it!
                        insts.add(PositiveResponsivenessInstance(base, x, raised))

        return insts

    def getInstancesMentioning(self, profile):
        raise NotImplementedError("Implement me!")

    def _updateProfile(self, profile, oldBallot, newBallot):
        """Substitute a ballot in a profile with a new one."""

        # Get the profile dict
        p_dict = profile.as_dict()

        # Remove the old ballot.
        p_dict[oldBallot] -= 1
        if p_dict[oldBallot] == 0:
            del p_dict[oldBallot]

        # Add the new one.
        if newBallot in p_dict:
            p_dict[newBallot] += 1
        else:
            p_dict[newBallot] = 1

        return model.AnonymousProfile(p_dict)

    def getInstancesMentioningHeuristic(self, profile, heur_info = None):
        insts = set()

        # In this heuristic, we generate only the "one-step" increases (exactly 1 voter raises the support of 1 step).

        # General idea: for every alternative, and for every unique ballot, we lift that alternative
        # of one "step". In this way, we obtain a new profile (and an instance). 

        for x in profile.alternatives:
            for b in profile.uniqueBallots():

                # Get the rank (position) of alternative in the ballot.
                index = b.rank(x) - 1

                # If we can lower it, create new ballot by lowering of one step x.
                if index < len(b) - 1:
                    
                    new_ballot = list(b)
                    new_ballot[index] = new_ballot[index+1]
                    new_ballot[index+1] = x

                    # Create new profile with this.
                    p = self._updateProfile(profile, b, model.AnonymousPreference(new_ballot))

                    # Create instance: base is the original profile, lifted is the new profile.
                    insts.add(PositiveResponsivenessInstance(p, x, profile))
                    

                # This is to get the instance in the other direction. Similar to the above.
                if index > 0:
                    new_ballot = list(b)
                    new_ballot[index] = new_ballot[index-1]
                    new_ballot[index-1] = x
                    p = self._updateProfile(profile, b, model.AnonymousPreference(new_ballot))

                    # Order is important here! The first profile is the "original" one, the second
                    # is the one where the support was lifted.
                    insts.add(PositiveResponsivenessInstance(profile, x, p))

        return insts

    def tree_asp(self):
        """Return facts, rules, constraints for building the ASP tree."""
        facts, rules, constraints = [], [], []

        rules.append("localConditionsSatisfied(positiveresponsiveness(P1,X,P2,O), N):- profile(P1), alternative(X), profile(P2), node(N), outcome(O), alwaysWinIn(N, X, P1).")
        rules.append("localConditionsSatisfied(positiveresponsiveness(P1,X,P2,O), N):- profile(P1), alternative(X), profile(P2), node(N), outcome(O), not statement(N, P2, O).")

        constraints.append(":- step(positiveresponsiveness(P1,X,P2,O), N1, N2), outcome(O), node(N1), N1<N2, node(N2), profile(P2), statement(N1,P2,O), not statement(N2,P2,O), alwaysWinIn(N1, X, P1).")
        constraints.append(":- step(positiveresponsiveness(P1,X,P2,O), N1, N2), outcome(O), node(N1), N1<N2, node(N2), profile(P2), statement(N2,P2,O1), outcome(O1), O != O1, alwaysWinIn(N1, X, P1).")

        constraints.append(":- step(positiveresponsiveness(P1,X,P2,O), N1, N2), statement(N1,P1,O1), not statement(N2,P1,O1), outcome(O), outcome(O1), node(N1), N1<N2, node(N2), profile(P2), alwaysWinIn(N1, X, P1).")

        #

        constraints.append(":- step(positiveresponsiveness(P1,X,P2,O), N1, N2), outcome(O), node(N1), N1<N2, node(N2), profile(P2), not statement(N1, P2, O), 0 != #count {O1 : outcome(O1), statement(N2,P1,O1), inOutcome(X, O1)}.")
        constraints.append(":- step(positiveresponsiveness(P1,X,P2,O), N1, N2), outcome(O), node(N1), N1<N2, node(N2), profile(P2), not statement(N1, P2, O), statement(N1, P1, O1), not inOutcome(X, O1), outcome(O1), not statement(N2, P1, O1).")

        constraints.append(":- step(positiveresponsiveness(P1,X,P2,O), N1, N2), outcome(O), node(N1), N1<N2, node(N2), profile(P2), not statement(N1, P2, O), statement(N1, P2, O1), outcome(O1), not statement(N2, P2, O1).")

        return facts, rules, constraints
        

class PositiveResponsivenessInstance(Instance):

    """Instance of the `Positive Responsiveness` axiom."""

    def __init__(self, base, alternative, raised):
        self._base = base
        self._alternative = alternative
        self._raised = raised

        self._profiles = frozenset((self._base, self._raised))

    @property
    def axiom(self) -> Type[Axiom]:
        return PositiveResponsiveness

    def mentions(self):
        return self._profiles

    def as_SAT(self, encoding):
        cnf = []

        # If the alternative wins in base, it wins in the raised profile (read this as an implication).
        cnf.append([-encoding.encode(self._base, self._alternative), encoding.encode(self._raised, self._alternative)])

        for a in self._base.alternatives:
            if a != self._alternative:
                # If the alternative wins in the base profile, nothing else wins in the raised profile.
                cnf.append([-encoding.encode(self._base, self._alternative), -encoding.encode(self._raised, a)])

        return cnf

    def as_asp(self, encoding):
        base, raised = map(encoding.encode_profile, (self._base, self._raised))
        alt = encoding.encode_alternative(self._alternative)
        outcome = encoding.encode_outcome(model.AnonymousOutcome({self._alternative}))
        return [f"positiveresponsiveness({base},{alt},{raised},{outcome})"]

    def from_asp(self, fact: str, encoding, prettify = False) -> str:

        base, raised = map(lambda x : encoding.encode_profile(x, prettify = prettify), (self._base, self._raised))
        if prettify:
            return f"In profile {raised} alternative <i>{self._alternative}</i> gained support relative to profile {base}. Hence, by Responsiveness, if <i>{self._alternative}</i> is a (tied) winner in the latter, it must be the only winner in the former."
        else:
            return f"In profile {raised} alternative {self._alternative} gained support relative to profile {base}. Hence, by Responsiveness, if {self._alternative} is a (tied) winner in the latter, it must be the only winner in the former."

    def _isEqual(self, other):
        return self._profiles == other._profiles and self._alternative == other._alternative

    def _hashable(self):
        return self._profiles, self._alternative

    def __str__(self):
        return f"In profile ({self._raised}) alternative {self._alternative} gained support relative to profile ({self._base}). Hence, if {self._alternative} wins in the latter, it must be the only winner in the former."

class Reinforcement(InterprofileAxiom):

    """Axiom encoding a consistency condition."""

    def getInstances(self):

        # Idea: for all (unoredered!) pairs of numbers i,j in [1..n-1] (where n is the number of voters),
        # we sum all profiles of i and j voters to obtain a superprofile, and generate the corresponding instance.

        insts = set()

        n = self.scenario.nVoters

        # Loop over all pair of numbers:
        for n1 in range(1, n//2 + 1):
            for n2 in range(n1, n - n1 + 1):
                # Loop over all profiles of these sizes.
                for p1 in self.scenario.profilesOfSize(n1):
                    for p2 in self.scenario.profilesOfSize(n2):
                        # Get the superprofile and instance.
                        p = p1.mergeProfile(p2)
                        insts.add(ReinforcementInstance(p, p1, p2))

        return insts

    def _auxBinaryPartitions(self, acc, rest):

        """Auxilliary function to generate all binary partitions of a profile.

            This is a tail-recursive function. That is, we use the 'acc' (accumulator) variable to hold the result of the recursion so far,
            and then finally return it at the end.

            Parameters
            ----------
            acc : list
                The results of the recusion so far. Every element of the list corresponds to a possible way to partition the profile, and is a pair where:
                    The first element describes the partition. It is a list of tuples (ballot, X, Y). In the original profile, "ballot" was expressed by X+Y voters, and
                        in this partition we split X of them into the first subprofile, and Y of them in the second one.
                    The second is a boolean, saying whether this partition is symmetric or not (that is, whether if we swap the first and second subprofile, we obtain the same partition).
                        This is useful for performance reasons.
            rest : list
                The rest of the ballots to process. It is a list of tuples, where each tuple has form (AnonymousPreference, int) (that is, a ballot and the number of voters who cast it).

            Returns
            -------
            list
                A list of the same form of the "acc" argument.
        """

        # Get the next ballot to process.
        ballot, counter = rest[0]

        # If acc is nonempy:
        if acc:
            acc_new = []
            # `split` iterates over all possible ways to split counter (the number of voters expressing this ballot) in two numbers.
            for split in range(counter // 2 + 1):

                # Are we splitting this number in two equal partitions (useful for optimisation)?

                isSymmetric = (split == counter - split)

                # For every possible (incomplete) partition,

                for possible_world, isSymmetricPrime in acc:
                    # Add this way of splitting this ballot to this partition, and check whether it is symmetric (this number and the rest must be)

                    acc_new.append((possible_world + [(ballot, split, counter - split)], isSymmetric and isSymmetricPrime))
                    # If this (new) way of splitting and the incomplete partition are both non-symmetric, we also have to add the opposite way to splitting the 
                    # current ballot.
                    if not isSymmetric and not isSymmetricPrime:
                        acc_new.append((possible_world + [(ballot, counter - split, split)], False))

        # If it is empy, it is the first turn.
        else:
            # Hence, 
            acc_new = [([(ballot, split, counter - split)], split == counter - split) for split in range(counter // 2 + 1)]


        if rest[1:]:
            return self._auxBinaryPartitions(acc_new, rest[1:])
        else:
            return acc_new

    def _binaryPartitions(self, profile):

        """Return all pairs of subprofiles of the input profile.

                    Parameters
            ----------
            profile : AnonymousProfile
                The profile to split.

            Returns
            -------
            set
                A set of pair of profiles.
            """

        # See the docs for this function.
        partitions = self._auxBinaryPartitions([], list(profile.ballotsWithCounts()))

        result = set()
        # 'partition` contains, for every ballot, the number of voters for the first and the second subprofiles who get this ballot.'
        for partition, _ in partitions:

            # The two subprofiles dictionaries.
            left_partition, right_partition = {}, {}

            # This is just to check whether the profile has at least one voter.
            l1, l2 = 0, 0

            for ballot, c1, c2 in partition:
                l1 += c1
                l2 += c2
                if c1 > 0:
                    left_partition[ballot] = c1
                if c2 > 0:
                    right_partition[ballot] = c2

            if l1 > 0 and l2 > 0:
                profile1 = model.AnonymousProfile(dict(left_partition))
                profile2 = model.AnonymousProfile(dict(right_partition))
                result.add((profile1, profile2))

        return result

    def _auxGenerateInstances(self, profile, sizeOfBallotsToAdd : int):

        """Return the instances of where profile is the superprofile, and where profile is a subprofile to which we add up to sizeOfBallotsToAdd ballots."""

        # profile is the superprofile.
        insts = {ReinforcementInstance(profile, first, second) for first, second in self._binaryPartitions(profile)} if len(profile) > 1 else set()

        # Other way around: we have a subprofile, get all the superprofiles with up to |profile|+sizeOfBallotsToAdd voters.

        if len(profile) < self.scenario.nVoters :

            for new_profile in self.scenario.profilesUpToSize(sizeOfBallotsToAdd):

                    superprofile = profile.mergeProfile(new_profile)

                    insts.add(ReinforcementInstance(superprofile, profile, new_profile))

        return insts

    def getInstancesMentioning(self, profile):
        return self._auxGenerateInstances(profile, self.scenario.nVoters - len(profile))

    def getInstancesMentioningHeuristic(self, profile, heur_info = None):
        # Only add one ballot in this heuristic.
        return self._auxGenerateInstances(profile, 1)

    def tree_asp(self):
        """Return the ASP facts, rules and constraints necessary to encode the Reinforcement rule."""
        facts = []
        rules = []
        constraints = []

        # Setting priority (Second largest for interprofile axioms)
        #rules.append("priority(2, reinforcement(P1,P2,P)) :- instance(reinforcement(P1,P2,P)), profile(P1), profile(P2), profile(P).")

        ### Instance might be usable if rule-specific conditions are met
        # Here, usable if P1 and P2 both have a finale outcome MIGHT NOT NECESSARY, and the instersection of these outcomes is not empty
        rules.append("localConditionsSatisfied(reinforcement(P1,P2,P),N):- profile(P1), outcome(O1), profile(P2), outcome(O2), profile(P), node(N), finaleOutcome(N,P1,O1), finaleOutcome(N,P2,O2), outcome(O), O != oEmpty, isIntersection(O,O1,O2).")


        ### Description of consequences
        # Using it actually prevents any outcome different from F(P1) \cap F(P2) to be possible for P if it was possible
        constraints.append(":- step(reinforcement(P1,P2,P), N1, N2), instance(reinforcement(P1,P2,P)), profile(P1), profile(P2), profile(P), node(N1), node(N2), N1 < N2, finaleOutcome(N,P1,O1), finaleOutcome(N,P2,O2), isIntersection(O,O1,O2), statement(N1,P,O), statement(N2,P,O3), outcome(O3), O3 != O.")

        # Otherwise, if intersection was not possible, we reach a contradiction and (P,oEmpty) is the only statement in N2 for P
        constraints.append(":- step(reinforcement(P1,P2,P), N1, N2), instance(reinforcement(P1,P2,P)), profile(P1), profile(P2), profile(P), node(N1), node(N2), N1 < N2, finaleOutcome(N,P1,O1), finaleOutcome(N,P2,O2), isIntersection(O,O1,O2), not statement(N1,P,O), not statement(N2,P,oEmpty).")

        ### Avoid side effects
        # Sutor ne ultra crepidam (wrt P1's outcome)
        constraints.append(":- step(reinforcement(P1,P2,P), N1, N2), instance(reinforcement(P1,P2,P)), profile(P1), profile(P2), profile(P), node(N1), node(N2), N1 < N2, statement(N1,P1,O), outcome(O), not statement(N2,P1,O).")

        # Sutor ne ultra crepidam (wrt P2's outcome)
        constraints.append(":- step(reinforcement(P1,P2,P), N1, N2), instance(reinforcement(P1,P2,P)), profile(P1), profile(P2), profile(P), node(N1), node(N2), N1 < N2, statement(N1,P2,O), outcome(O), not statement(N2,P2,O).")

        return facts, rules, constraints
        
class ReinforcementInstance(Instance):

    """Instance of the `Reinforcement` axiom."""

    def __init__(self, p, p1, p2):
        self._profile = p
        self._part1, self._part2 = p1, p2

        self._profiles = frozenset((p, p1, p2))

    @property
    def axiom(self) -> Type[Axiom]:
        return Reinforcement

    def mentions(self):
        return self._profiles

    def _isEqual(self, other) -> bool:
        return self._profiles == other._profiles

    def _hashable(self):
        return self._profiles

    def as_SAT(self, encoding):
        cnf = []

        # This CNF It's kinda hard to see... For all alternatives,
        for x in self._profile.alternatives:
            # Literal expressing that x wins in superprofile.
            literal = encoding.encode(self._profile, x)
            # If x loses in superprofiles, then it loses in either of the subprofiles. Note that
            # -literal -> (-... OR -...) can be written as literal OR -... -...
            cnf.append([-encoding.encode(self._part1, x), -encoding.encode(self._part2, x), literal])

            # Furthermore, for all other alternatives y, it holds that:
            for y in self._profile.alternatives:
                if x != y:
                    # If x wins in superprofile, then: either y loses in a subprofile or x wins in part1.
                    # If x wins in superprofile, then: either y loses in a subprofile or x wins in part2.

                    # Since these must hold both, it's basically saying that if x wins, then it must either win in both x or 
                    # that the intersection is empty
                    cnf.append([-literal, encoding.encode(self._part1, x), -encoding.encode(self._part1, y), -encoding.encode(self._part2, y)])
                    cnf.append([-literal, encoding.encode(self._part2, x), -encoding.encode(self._part1, y), -encoding.encode(self._part2, y)])

        return cnf

    def as_asp(self, encoding):
        p1, p2 = map(encoding.encode_profile, sorted((self._part1, self._part2)))
        p = encoding.encode_profile(self._profile)
        return [f'reinforcement({p1},{p2},{p})']

    def from_asp(self, fact : str, encoding, prettify = False) -> str:
        p1, p2 = map(lambda x : encoding.encode_profile(x, prettify = prettify), sorted((self._part1, self._part2)))
        p = encoding.encode_profile(self._profile, prettify = prettify)
        if self._part1 != self._part2:
            return f"Observe that, when we merge profiles {p1} and {p2}, we obtain {p}. Hence, by Reinforcement, the alternatives that win both under {p1} and {p2} must be the winners of {p}."
        else:
            return f"Profile {p} can be obtained by duplicating {p1}. Thus, by Reinforcement, their outcomes must be the same."

    def __str__(self):
        if self._part1 != self._part2:
            return f"If some alternatives win in both ({self._part1}) and ({self._part2}), they must be the outcome of ({self._profile})."
        else:
            return f"Profile ({self._profile}) can be obtained by duplicating ({self._part1}). Thus their outcomes must be the same."
