import unittest

from math import factorial

import COMSOC.anonymous as theory

class TestAnonymous(unittest.TestCase):

    def setUp(self):
        sizes = [(5, 3), (3, 4), (3, 3), (2, 5)]
        self.scenarios = {(n, m) : theory.Scenario(n, map(str, range(m))) for n, m in sizes}

    def test_readFromString(self):
        """Test whether the right profiles are created from string."""
        scenario3x3 = self.scenarios[(3, 3)]

        profile = theory.Profile({theory.Preference(('0', '1', '2')): 1, theory.Preference(('2', '1', '0')): 2})

        strings = ["0>1>2,2:2>1>0", "0>1>2,2>1>0,2>1>0", "2>1>0,0>1>2,2>1>0", "1:0>1>2,2:2>1>0"]

        for string in strings:
            self.assertEqual(scenario3x3.get_profile(string), profile)

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

            borda = theory.rules.Borda(scenario)

            indexes = {}
            model = []

            for profile in scenario.profiles:
                for alternative in scenario.alternatives:

                    e = scenario.SATencoding.encode(profile, alternative)

                    # Is it new?
                    self.assertNotIn(e, indexes)
                    # Not zero (SAT solvers want non-zero encodings)?
                    self.assertNotEqual(0, e)

                    indexes[e] = (profile, alternative)

                    if alternative in borda(profile):   
                        model.append(e)
                    else:
                        model.append(-e)

            # Check shape of ENCODING dictionary

            # Do they start from 1? (Important for MARCO solver)
            self.assertIn(1, scenario.SATencoding._profileAlt2index.values())
            # Is it contiguous?
            self.assertEqual(max(scenario.SATencoding._profileAlt2index.values()), len(scenario.SATencoding._profileAlt2index.values()))

            # Try decoding.
            for index, (profile, alternative) in indexes.items():
                self.assertEqual(scenario.SATencoding.decode(index), (profile, alternative))

            # Check whether Borda is correctly encoded
            self.assertEqual(borda.as_SAT(scenario.SATencoding), model)

            # Check whether the BORDA rule agrees with its (decoded) encoding.
            decoded = scenario.decodeSATModel(model)

            for profile in scenario.profiles:
                self.assertEqual(borda(profile), decoded(profile))


    def test_borda(self):
        """Test whether the implementation of the Borda rule works properly."""

        # Mapping from profiles to the expected Borda outcomes.
        scenario3x3 = self.scenarios[(3, 3)]

        borda_outcomes = {
            scenario3x3.get_profile('0>1>2') : scenario3x3.get_outcome('0'),
            scenario3x3.get_profile('0>1>2,2>1>0') : scenario3x3.get_outcome('0,1,2'),
            scenario3x3.get_profile('1:0>1>2,2:2>0>1') : scenario3x3.get_outcome('0,2'),
            scenario3x3.get_profile('0>1>2,1>0>2') : scenario3x3.get_outcome('0,1'),
        }

        borda = theory.rules.Borda(scenario3x3)

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
                self.assertEqual(profile, theory.Profile(dict(profile.ballotsWithCounts())))
                self.assertEqual(len(profile), sum((c for _, c in profile.ballotsWithCounts())))

        #TODO: Finish here

        #TODO: Check whether, if I modify something from an iterable (e.g., preferences from profile), I don't edit the profile?


    def test_topFunction(self):
        """Test whether the top function works for singleton profiles."""
        self.assertEqual('0', self.scenarios[(3, 3)].get_profile('1:0>1>2').top())
        self.assertEqual('1', self.scenarios[(3, 3)].get_profile('1:1>0>2').top())
        self.assertEqual('2', self.scenarios[(3, 3)].get_profile('1:2>0>1').top())

    @unittest.expectedFailure
    def test_topFunctionFailure(self):
        """Test whether the top function fails for non-singleton profiles."""
        self.scenarios[(3, 3)].get_profile('2:0>1>2').top()
        self.scenarios[(3, 3)].get_profile('3:0>1>2').top()

# TODO: Profiles, Axioms

if __name__ == '__main__':
    unittest.main()