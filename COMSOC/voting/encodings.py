from typing import List

class SATEncodingHandler:

    def __init__(self):

        # These data structures are needed for SAT solving. They are used to map
        # all possible (profile, alternative) pairs into a positive integer.

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

class ASPEncodingHandler:

    def __init__(self):

        self._prof2str = {}
        self._str2prof = {}

        self._alt2str = {}
        self._str2alt = {}

        self._out2str = {}
        self._str2out = {}

    def prettify_profile(self, profile):
        num = profile[1:]
        return f"<i>R</i><sub>{num}</sub>" if int(num) != 0 else f"<i>R</i><sup>*</sup>"  # assumption: 0 is the goal profile.

    def encode_profile(self, profile, prettify = False):
        if not profile in self._prof2str:
            string = 'p' + str(len(self._prof2str))
            self._prof2str[profile] = string
            self._str2prof[string] = profile

        result = self._prof2str[profile]

        if prettify:
            result = self.prettify_profile(result)

        return result

    def encode_alternative(self, alternative):
        if not alternative in self._alt2str:
            string = 'a_' + str(alternative)
            self._alt2str[alternative] = string
            self._str2alt[string] = alternative

        return self._alt2str[alternative]

    def encode_outcome(self, outcome):
        if not outcome in self._out2str:
            string = 'o_' + '_'.join(map(str, sorted(outcome)))
            self._out2str[outcome] = string
            self._str2out[string] = outcome

        return self._out2str[outcome]

    def decode(self, item: str):
        if item[0] == 'p':
            return self._str2prof[item]
        elif item[0] == 'a':
            return self._str2alt[item]
        elif item[0] == 'o':
            return self._str2out[item]
        else:
            raise NotImplementedError()