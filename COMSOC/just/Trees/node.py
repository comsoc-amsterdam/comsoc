# This should be part of its own module TODO

class Node():
    'Represent a node in a proof tree.'

    def __init__(self, id):
        self.id = id
        self.statements = []

    def __hash__(self):
        return int(self.id)

    def __repr__(self):
        return "N" + self.id

    def getID(self):
        """return the node ID for quick identification."""
        return self.id

    def addStatement(self, statement):
        """Add a statement to the node."""

        self.statements.append(statement)

    def getStatements(self):
        """Return the list of statements associated with the node."""
        return self.statements

    def getMentionedProfiles(self):
        """Return the list of profiles mentioned in this node."""
        res = {}

        for statement in self.statements:
            res[statement.getProfile()] = 1

        return res.keys()

    def getStatementsforProfile(self, profile):
        """Return the list of Statements regarding profile."""
        res = []

        for statement in self.statements:
            if statement.getProfile() == profile:
                res.append(statement)

        return res

    def getLabel(self):
        """Return the string used to annotate the node when drawing it."""

        label = "N" + self.id + ":\\n"

        for profile in self.getMentionedProfiles():
            strStatement = "F(" + profile + ") in "
            strStatement += "{"

            for statement in self.getStatementsforProfile(profile):
                outcome = statement.getOutcome()
                strStatement += str(outcome) + ", "
                #outcome = outcome.replace("o","")
                #if outcome != "Empty":
                    #outcome = "{" + ",".join([str(c) for c in outcome]) + "}"
                #else:
                    #outcome = "{}"
                #strStatement += outcome +", "

            strStatement = strStatement[:-2]
            strStatement += "}\\n"
            label += strStatement

        return label
