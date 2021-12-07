class Statement():
    'Represent a statement regarding a profile'

    def __init__(self, profile, outcome):
        self.profile = profile
        self.outcome = outcome

    def __repr__(self):
        return "(" + self.profile + "," + str(self.outcome) + ")"

    def getProfile(self):
        """Return the profile associated to the statement."""
        return self.profile

    def getOutcome(self):
        """Return the outcome associated to the statement."""
        return self.outcome

    def toString(self):
        """Provide a textual representation of statement."""

        return "(" + self.profile + "," + str(self.outcome) + ")"
