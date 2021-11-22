from COMSOC.interfaces.model import AbstractScenario, AbstractProfile
from COMSOC.voting.model import VotingOutcome, VotingPreference
from COMSOC.anonymous.rules import AnonymousRule

from typing import Dict, Iterator, List, Callable, Set

from COMSOC.helpers import powerset, merge_dicts
from itertools import permutations, combinations
from collections import defaultdict, Counter

from math import factorial
from scipy.special import comb

class AnonymousScenario(AbstractScenario):
    """Class representing an anonymous voting scenario"""

    @classmethod
    def _profileDictFromString(self, description):
        """ Create a dictionary that maps ballots to integers from a string description.

            Two variants:
            `0>1>2,0>1>2,2>1>0` or `2:0>1>2,1:2>1>0` mean the same thing. In the
            latter example, you can omit the `1:`.
            """
        if ':' in description:
            # Count:Ballot 
            profile_dict = {}
            for countBallotString in description.split(','):
                if ':' in countBallotString:
                    count_str, ballot_str = countBallotString.split(':')
                    ballot = AnonymousPreference(x for x in ballot_str.split('>'))
                    count = int(count_str)
                # : omitted means implicitly that count is 1.
                else:
                    ballot = AnonymousPreference(x for x in countBallotString.split('>'))
                    count = 1
                profile_dict[ballot] = count
        else:
            profile_dict = {}
            for ballot_str, count in Counter(description.split(',')).items():
                ballot = AnonymousPreference(x for x in ballot_str.split('>'))
                profile_dict[ballot] = count
        
        return profile_dict

    @classmethod
    def scenarioAndProfileFromString(cls, description: str):
        """Return a (scenario, profile) pair from a string description.


        If the string describes a profile of N voters and M alternatives, return a scenario
        with N voters and M alternatives and the described profile.
        Two variants:
        `012,012,210` or `2:012,1:210` mean the same thing. In the
        latter example, you can omit the `1:`.

        """

        # get the dictionary description of the profile
        profile_dict = cls._profileDictFromString(description)

        # The number of voters is the total of the counts.
        nVoters = sum(profile_dict.values())
        # Get any ballot; its length is the number of alternatives.
        for anyBallot in profile_dict:
            nAlternatives = len(anyBallot)
            break

        # Make the scenario and return it.
        scenario = cls(nVoters, anyBallot)

        return scenario, AnonymousProfile(profile_dict)


    def __init__(self, nVoters: int, alternatives: Iterator):
        self._nVoters = nVoters
        self._alternatives = frozenset(alternatives)

        # This stores all profiles by length (used to avoid generating profiles twice; we sacrifice
        # memory for time).
        self._profilesByLength = {}
    

    @property
    def nProfiles(self) -> int:
        """Return the number of profiles in this scenario."""
        m = len(self.alternatives)
        sub_count = lambda n : comb(n+factorial(m)-1, n)

        return sum(sub_count(k) for k in range(1, self.nVoters+1))

    @property
    def theory(self):
        import COMSOC.anonymous
        return COMSOC.anonymous

    @property
    def nVoters(self):
        """Return the number of voters."""
        return self._nVoters
    
    @property
    def alternatives(self):
        """Return the number of alternatives."""
        return self._alternatives

    @property
    def defaultAxioms(self) -> Set:
        # TODO: I import this here to avoid cyclic imports; find a better way to do this?
        return {self.theory.axioms.AtLeastOne(self)}

    def get_outcome(self, description):
        """Given a string, return the corresponding outcome.

        Example: 0,1,2 returns {0, 1, 2}.
        """
        return AnonymousOutcome(description.split(','))

    def get_profile(self, description: str):
        """ Given a profile description, return the profile.

        Two variants:
        `012,012,210` or `2:012,1:210` mean the same thing. In the
        latter example, you can omit the `1:`.
        """
        return AnonymousProfile(self._profileDictFromString(description))
        

    def _generateProfilesOfSize(self, n: int):
        """Auxilliary function used to generate all profiles.

            In this function, we initialise the value of dictionary _profilesByLength in n.
            It works recursively by adding all possible ballots to all possible profiles with (n-1) voters.

            Parameters
            ----------
            n : int
                Number of voters.

            Returns
            -------
            None
        """

        # TODO: make it online, that is, yield profiles as you create them. Problem: make it work with the other function that call this one.

        # If we have only one voter, we just return the dictionaries corresponding to all singleton profiles.
        if n == 1:
            newProfiles = {AnonymousProfile({preference: 1}) for preference in self.preferences}
        elif n <= self.nVoters:
            # Recursive call with n-1 voters. With this, we can obtain all profiles with n voters
            # by just adding one ballot (for every possible ballot) to every profile with n-1 voters.
            smallerProfiles = self.profilesOfSize(n-1)
            newProfiles = set()
            # For every profile with n-1 voters and for every possible preference, add this preference to the profile.
            for profile in smallerProfiles:
                for preference in self.preferences:
                    pdict = profile.as_dict()
                    if preference in pdict:
                        pdict[preference] += 1
                    else:
                        pdict[preference] = 1
                    # Add the resulting profile to the bunch.
                    newProfiles.add(AnonymousProfile(pdict))
        else:
            raise Exception(f"This scenario only has {self.nVoters}, but you tried generating profiles for {n}.")

        self._profilesByLength[n] = newProfiles

    def profilesOfSize(self, n: int) -> Set:

        """Return the set of all profiles with exactly n voters."""

        # If we have already generated the profiles with exactly n voters, we return that.
        try:
            return self._profilesByLength[n]
        # Otherwise, we initalise that, and return it.
        except KeyError:
            self._generateProfilesOfSize(n)
            return self._profilesByLength[n]

    def profilesUpToSize(self, n: int) -> Iterator:
        """Iterate over all profiles with up to n voters."""
        for size in range(1, n+1):
            for p in self.profilesOfSize(size):
                yield p

    @property
    def profiles(self) -> Iterator:
        """Return all profiles in this scenario."""
        return self.profilesUpToSize(self.nVoters)

    @property
    def preferences(self) -> Iterator:
        """Return all possible preference orders for this scenario."""
        return {AnonymousPreference(perm) for perm in permutations(self.alternatives)}

    @property
    def outcomes(self) -> Iterator:
        """Return all possible voting outcomes for this scenario."""
        return {AnonymousPreference(outcome) for outcome in powerset(self.alternatives) if outcome}

    def decodeSATModel(self, model: List[int]) -> dict:
        """Given a SAT model (list of non-zero integers), return a SCF that
        is consistent with this model."""

        # Dictionary from profiles to set of alternatives, representing the possible winner.
        # By default, we return all alternatives.
        possibleWinners = defaultdict(lambda : set(self.alternatives))
        # For every literal, if that literal is negative, we remove
        # the corresponding alternative from the possible winners of the corresponding profile.
        for literal in model:
            if literal < 0:
                profile, alt = self.theory.SATencoding.decode(literal)
                possibleWinners[profile].remove(alt)
            # If it is positive, nothing to do: we already have all possible winners there.

        # Alternative: randomise (select random subset of possible winners).

        # Return the corresponding function.
        return AnonymousRule.from_function(lambda p: possibleWinners[p], self)

    def __str__(self):
        alt_str = '{' + ', '.join(map(str, sorted(self.alternatives))) + '}'
        return f"Anonymous voting scenario, with {self.nVoters} voters and alternatives {alt_str}."


class AnonymousPreference(VotingPreference):
    """Class representing an individual preference in anonymous voting. Identical to a voting preference."""
    pass

class AnonymousOutcome(VotingOutcome):
    """Class representing a possible outcome in anonymous voting. Identical to a voting outcome."""
    pass

class AnonymousProfile(AbstractProfile):
    """Class representing an anonymous preference profile."""

    def __init__(self, preferences: Dict[AnonymousPreference, int]):
        """Initialise the profile."""
        self._profile = preferences
        self._name = ", ".join("#" + str(count) + ":" + str(ballot) for ballot, count in sorted(self._profile.items()))
        self._length = sum(preferences.values())
        self._alternatives = frozenset(self.anyBallot())

    @property
    def alternatives(self):
        """Return the alternatives of this profile."""
        return self._alternatives

    def top(self):
        """If this profile is a singleton (one voter), return its top-ranked alternative."""
        assert len(self) == 1, "This function can only be called on singleton profiles."
        return self.anyBallot().top()

    def ballotsWithCounts(self) -> Iterator:
        """Return an iterator over tuples of form (ballot : AnonymousPreference, count : int) describing the profile."""
        return self._profile.items()

    def uniqueBallots(self):
        """Return all unique ballots."""
        return self._profile.keys()

    def anyBallot(self):
        """Return any ballot in the profile."""
        for b in self.uniqueBallots():
            return b

    def isParetoDom(self, x) -> bool:
        """Check whether some alternative x is Pareto-domianted."""

        # Does y dominated x?
        for y in self.alternatives:
            if x != y:
                # Assume it does...
                flag = True
                # Check all (unique ballots)
                for ballot in self.uniqueBallots():
                    # If x is preferred to y, we are proved wrong.
                    if ballot.prefers(x, y):
                        flag = False
                        break
                # If we are never proven wrong, return True!
                if flag:
                    return True
        # We couldn't find any y that Pareto-dominates x.
        return False


    def majorityContest(self, x, y) -> Set:
        prefer_x, prefer_y = 0, 0
        for ballot, count in self.ballotsWithCounts():
            if ballot.prefers(x, y):
                prefer_x += 1
            else:
                prefer_y += 1

        if prefer_x > prefer_y:
            return {x}
        elif prefer_x < prefer_y:
            return {y}
        else:
            return {x, y}

    def condorcetWinner(self):
        disproven = set()

        for x in self.alternatives:
            if x in disproven:
                continue
            for y in self.alternatives:
                if x != y:
                    winner = self.majorityContest(x, y)
                    if len(winner) > 1:
                        return None
                    elif x in winner:
                        disproven.add(y)
                    else:
                        disproven.add(x)
                        break
            if not x in disproven:
                return x

    def hasCondorcetWinner(self):
        return not (self.condorcetWinner() is None)

    def isPerfectTie(self) -> bool:
        """Check whether this profile is a perfect tie (as defined in the Cancellation axiom)."""

        # Can only happen for profile with an even amount of voters.
        if len(self) % 2 != 0:
            return False

        # For every (unordered) pair of alternatives x, y
        for x, y in combinations(self.alternatives, 2):
            # If they don't tie, this is not a perfectly-tied profile.
            if len(self.majorityContest(x, y)) < 2:
                return False

        # We were never proven wrong: return True.
        return True

    def mergeProfile(self, other):
        """Merge this profile with another profile from the same scenario."""
        return AnonymousProfile(merge_dicts(self._profile, other._profile))

    def as_dict(self):
        """Returnt this profile as a dictionary mapping ballots to integers."""
        return dict(self._profile)
    
    def __str__(self):
        return self._name

    def __eq__(self, other):
        """Check whether this profile is the same as another."""
        return self._profile == other._profile

    def __hash__(self):
        return hash(str(self))

    def __gt__(self, other):
        """Check lexicographic ordering of two profiles."""
        return self._name > other._name

    def __len__(self):
        """Return the number of voters."""
        return self._length
