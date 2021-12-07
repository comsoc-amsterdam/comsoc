# This should be part of its own module TODO

class Edge():
    'Represent an edge in a proof tree.'

    def __init__(self, src, dest):
        self.src = src
        self.dest = dest
        self.step = "default step"

    def getSrc(self):
        """Return the source node of the edge."""
        return self.src

    def getDest(self):
        """Return the destination node of the edge."""
        return self.dest

    def getStep(self):
        """Return the step associated to the edge."""
        return self.step

    def linkToStep(self, step):
        """Link the edge to a specific step in the proof."""

        # Raw step is added, need to add more granularity TODO
        self.step = step
