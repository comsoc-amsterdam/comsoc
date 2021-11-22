from typing import List

class SATEncodingHandler:

    def __init__(self):

        # These data structures are needed for SAT solving. They are used to map
        # all possible (profile, alternative) pairs into a positive integer.
        # TODO: do it a-priori by only looking at the integer, without the datastructure, that is
        # create a bijection from anon-profiles to natural numbers... Also, make it consistent across
        # different runs, and across scenarios of different size: that is, if a profile P can be in two scenarios 
        # S and S', it should have the same index (for the same alternative) in both.

        # Counter used to generate the indexes.
        self._counter = 0
        # Maps (profile, alternative) into an integer and viceversa.
        self._profileAlt2index = dict()
        self._index2profileAlt = dict()

    def encode(self, profile, alternative) -> int:
        """Given a profile and an alternative, return a unique index for these two.

        Useful for SAT encodings."""

        # If we already have an index, return it.
        try:
            return self._profileAlt2index[(profile, alternative)]
        # Otherwise, create it, and return it. We use self._counter to keep track of the unique indexes so far.
        # Note that the first index is 1. This is because most sat solver don't like 0-indexes.
        except KeyError:
            self._counter += 1
            self._profileAlt2index[(profile, alternative)] = self._counter
            self._index2profileAlt[self._counter] = (profile, alternative)
            return self._counter

    def decode(self, i: int):
        """Given a unique index, return the corresponding profile and alternative.

        We assume that we already know the index of the profile and alternative (it is in the dictionary).
        Useful for decoding SAT models."""

        return self._index2profileAlt[abs(i)]

