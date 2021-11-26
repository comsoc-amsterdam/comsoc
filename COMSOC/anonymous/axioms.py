from COMSOC.interfaces.axioms import Axiom, IntraprofileAxiom, InterprofileAxiom,\
    Instance, DerivedAxiomInstance, DerivedAxiom
import COMSOC.anonymous.model as model

from typing import List, Set, Type
from itertools import permutations, combinations

########### INTRAPROFILE AXIOMS ################

class AtLeastOne(IntraprofileAxiom):

    """Axiom encoding the fact that, for every profile, at least one alternative must win."""

    def getInstances(self) -> Set:
        return {AtLeastOneInstance(profile) for profile in self.scenario.profiles}

    def getInstancesMentioning(self, profile) -> Set:
        return {AtLeastOneInstance(profile)}

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

class FaithfulnessInstance(Instance):

    """Instance of the Faitfhulness Axiom."""

    def __init__(self, profile):
        self._profile = profile

    @property
    def axiom(self) -> Type[Axiom]:
        return Faitfhulness

    def mentions(self):
        return {self._profile}

    def _isEqual(self, other) -> bool:
        return self._profile == other._profile

    def _hashable(self):
        return self._profile

    def as_SAT(self, encoding) -> List[List[int]]:
        # The CNF is made of singleton clauses. For every alternative, we hace one clause stating that it must win 
        # (if it is the top ranked one) or lose (otherwise)
        return [[(1 if x == self._profile.top() else -1) * encoding.encode(self._profile, x)] for x in self._profile.alternatives]

    def __str__(self):
        return f"In profile ({self._profile}) there is only one voter. Hence, their favorite alternative should win."

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

    def __str__(self):
        return f"In profile ({self._profile}) alternative {self._dominated} is Pareto-dominated. Hence, it cannot win."        

class Cancellation(IntraprofileAxiom):

    """Axiom encoding the fact that, if all alternatives tie in majority contests, all alternatives win."""

    def getInstances(self) -> Set:
        return {CancellationInstance(profile) for profile in self.scenario.profiles if profile.isPerfectTie()}

    def getInstancesMentioning(self, profile) -> Set:
        return {CancellationInstance(profile)} if profile.isPerfectTie() else set()

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

    def __str__(self):
        return f"Profile ({self._profile}) is a perfect tie: all alternatives must win here."

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

    def _isEqual(self, other):
        return self._profiles == other._profiles and self._mapping == other._mapping

    def _hashable(self):
        return self._profiles, self._mapping

    def __str__(self):
        return f"Profiles ({self._base}) and ({self._mapped}) are identical up to a renaming of the alternatives: {self._mapping}. Hence, the outcomes must be equal under the same renaming."

class PositiveResponsiveness(InterprofileAxiom):

    """Axiom encoding the fact that if a (possibly tied) alternative receives increased support, then it must be the unique winner."""

    def getInstances(self):
        raise NotImplementedError("Implement me!")

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

    def _isEqual(self, other):
        return self._profiles == other._profiles and self._alternative == other._alternative

    def _hashable(self):
        return self._profiles, self._alternative

    def __str__(self):
        return f"In profile ({self._raised}) alternative {self._alternative} gained support from profile ({self._base}). Hence, if {self._alternative} wins in the latter, it must be the only winner in the former."

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

    def __str__(self):
        return f"Since profile ({self._profile}) can be obtained by combining ({self._part1}) and ({self._part2}), then whenever the intersection of F({self._part1}) and F({self._part2}) is non-empty, it must be equal to F({self._profile})."


########### HEURISTICS ################

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
                    new_profile_dict[model.AnonymousPreference(new_ballot)] = c

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