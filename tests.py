import unittest

from math import factorial

from COMSOC.anonymous.rules import borda
from COMSOC.anonymous.model import AnonymousScenario, AnonymousPreference, AnonymousOutcome, AnonymousProfile

class TestAnonymous(unittest.TestCase):

    def setUp(self):
        sizes = [(5, 3), (3, 4), (3, 3), (2, 5)]
        self.scenarios = {(n, m) : AnonymousScenario(n, map(str, range(m))) for n, m in sizes}

    def test_readFromString(self):
        """Test whether the right profiles are created from string."""
        scenario3x3 = self.scenarios[(3, 3)]

        profile = AnonymousProfile(scenario3x3, {AnonymousPreference(('0', '1', '2')): 1, AnonymousPreference(('2', '1', '0')): 2})

        strings = ["0>1>2,2:2>1>0", "0>1>2,2>1>0,2>1>0", "2>1>0,0>1>2,2>1>0", "1:0>1>2,2:2>1>0"]

        for string in strings:
            self.assertEqual(scenario3x3.profileFromString(string), profile)

    def test_scenarioSizes(self):
        """Test various sizes of scenarios."""

        for (n, m), scenario in self.scenarios.items():
            self.assertEqual(scenario.nVoters, n)
            self.assertEqual(len(scenario.alternatives), m)
            self.assertEqual(len(scenario.preferences), factorial(m))
            self.assertEqual(len(scenario.outcomes), 2**m-1)
        
    def test_profileGeneration(self):
        """Test whether the scenarios generate the expected amount of profiles."""

        for scenario in self.scenarios.values():
            self.assertEqual(len(list(scenario.profiles)), scenario.nProfiles)

        scenario3x3 = self.scenarios[(3, 3)]
        self.assertEqual(len(list(scenario3x3.profilesUpToSize(2)) + list(scenario3x3.profilesOfSize(3))),\
            scenario3x3.nProfiles)

    def test_satEncoding(self):
        """Test whether the SAT encoding of a scenario behaves as expected."""

        for scenario in self.scenarios.values():
            indexes = {}
            model = []

            for profile in scenario.profiles:
                for alternative in scenario.alternatives:

                    e = profile.encodeWithAlt(alternative)

                    # Is it new?
                    self.assertNotIn(e, indexes)
                    # Not zero (SAT solvers want non-zero encodings)?
                    self.assertNotEqual(0, e)

                    indexes[e] = (profile, alternative)

                    if alternative in borda(profile):   
                        model.append(e)
                    else:
                        model.append(-e)

            # Do they start from 1? (Important for MARCO solver)
            self.assertEqual(len(indexes.keys()), max(indexes.keys()))

            # Try decoding.
            for index, (profile, alternative) in indexes.items():
                self.assertEqual(scenario.decodeProfileAndAlt(index), (profile, alternative))

            # Check whether borda is correctly encoded
            self.assertEqual(scenario.getRuleSATModel(borda), model)

            # Check whether the BORDA rule agrees with its (decoded) encoding.
            decoded = scenario.decodeSATModel(model)

            for profile in scenario.profiles:
                self.assertEqual(borda(profile), decoded(profile))


    def test_borda(self):
        """Test whether the implementation of the Borda rule works properly."""

        # Mapping from profiles to the expected borda outcomes.
        scenario3x3 = self.scenarios[(3, 3)]

        borda_outcomes = {
            scenario3x3.profileFromString('0>1>2') : scenario3x3.outcomeFromString('0'),
            scenario3x3.profileFromString('0>1>2,2>1>0') : scenario3x3.outcomeFromString('0,1,2'),
            scenario3x3.profileFromString('1:0>1>2,2:2>0>1') : scenario3x3.outcomeFromString('0,2'),
            scenario3x3.profileFromString('0>1>2,1>0>2') : scenario3x3.outcomeFromString('0,1'),
        }

        # Check if they match everywhere.
        for profile, outcome in borda_outcomes.items():
            self.assertEqual(borda(profile), outcome)

    def test_profileProperties(self):
        """Test various properties of profiles."""

        scenario3x3 = self.scenarios[(3, 3)]
        scenario3x4 = self.scenarios[(3, 4)]

        for scenario in (scenario3x3, scenario3x4):
            for profile in scenario.profiles:
                self.assertEqual(profile.alternatives, scenario.alternatives)
                self.assertEqual(dict(profile.ballotsWithCounts()), profile.as_dict())
                self.assertEqual(profile, AnonymousProfile(scenario, dict(profile.ballotsWithCounts())))
                self.assertEqual(len(profile), sum((c for _, c in profile.ballotsWithCounts())))

        #TODO: Finish here

        #TODO: Check whether, if I modify something from an iterable (e.g., preferences from profile), I don't edit the profile?


    def test_topFunction(self):
        """Test whether the top function works for singleton profiles."""
        self.assertEqual('0', self.scenarios[(3, 3)].profileFromString('1:0>1>2').top())
        self.assertEqual('1', self.scenarios[(3, 3)].profileFromString('1:1>0>2').top())
        self.assertEqual('2', self.scenarios[(3, 3)].profileFromString('1:2>0>1').top())

    @unittest.expectedFailure
    def test_topFunctionFailure(self):
        """Test whether the top function fails for non-singleton profiles."""
        self.scenarios[(3, 3)].profileFromString('2:0>1>2').top()
        self.scenarios[(3, 3)].profileFromString('3:0>1>2').top()

# TODO: Profiles, Axioms

if __name__ == '__main__':
    unittest.main()