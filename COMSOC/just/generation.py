from collections import deque
from COMSOC.interfaces.model import AbstractProfile, AbstractOutcome, AbstractScenario
from COMSOC.interfaces.axioms import Instance, Axiom

from typing import Set, Iterator


class InstanceGraph:
    """An instance graph (of a given set of axioms)."""

    class Node:

        """A node of an instance graph."""

        def __init__(self, graph, profile: AbstractProfile):
            """Initialises a node of an instance graph correspondin to a profile. Sets some default values, such as whether the node is explored yet and the depth at which is found. Also, generates the intra-profile axioms instances regarding this node."""
            self._profile = profile

            # Tshe intra-profile instances of this node.
            self._instances = set()

            # Generate the intra-profile axioms regarding this node. 
            for axiom in graph.intraAxioms:
                # If the instsance graph is heuristic, use the heuiristic generation method instead.
                if graph.isHeuristic():
                    instances = axiom.getInstancesMentioningHeuristic(self.profile)
                else:
                    instances = axiom.getInstancesMentioning(self.profile)

                # Register the axiom creating the instances.
                for instance in instances:
                    instance.created_by = axiom

                # Add the instances to the node.
                self._instances.update(instances)

            # Add the generated instances to graph.
            graph.addInstances(self._instances)

            # By default, a generated node has not bee explored yet. And of course it's depth is unknown until we explore it.
            self._explored = False
            self._depth = None

            # Stores the axioms by which this node was reached.
            self._reachedBy = set()

        @property
        def profile(self):
            """Return the profile corresponding to the node."""
            return self._profile
        
        @property
        def instances(self):
            """Return the intra-profile axiom instances that mention the profile corresponding to the node."""
            return self._instances

        @property
        def depth(self):
            """Return the distance of this node from the starting node."""
            return self._depth
        
        @depth.setter
        def depth(self, value):
            """Update the depth of this node."""
            if self._depth is None or value < self._depth:
                self._depth = value

        def isExplored(self):
            """Check whether this node has been explored yet (that is, expanded)."""
            return self._explored

        def setExplored(self):
            """Signal that this node was indeed explored (that is, expanded)."""
            self._explored = True

        def setReachedBy(self, axiom):
            """Add an axiom to the set of axioms whose instances reach this node. Useful for heuristic purposes."""
            self._reachedBy.add(str(axiom))

        def getHeuristicInfo(self):
            """Return a dictionary containing information useful for heuristic purposes."""
            return {"reachedByNeutrality": "Neutrality" in self._reachedBy}

        def __eq__(self, other):
            return self.profile == other.profile

        def __hash__(self):
            return hash(self.profile)

        def __str__(self):
            return "NODE(" + str(self.profile) + ")"

    #### Back to the Graph! ####

    def __init__(self, axioms: Set[Axiom], heuristics = False):
        """Initalises the instance graph, given a set of axioms. The `heuristics` parameter controls whether we should use the heuristic strategies during search."""
        self._intraAxioms = {axiom for axiom in axioms if axiom.isIntra()}
        self._interAxioms = {axiom for axiom in axioms if not axiom.isIntra()}
        self._axioms = axioms
        self._heuristics = heuristics
        self._instances = set()

        # This is used to map a profile to the corresponding node. We use this datastructure so to that, for any profile, we always have access to its (unique) corresponding Node object.
        # This is useful, as some persistant information is stored in the nodes.
        self._p2n = dict()

    @property
    def axioms(self):
        """Return the axioms of the instance graph."""
        return self._axioms

    @property
    def intraAxioms(self):
        """Return the intraprofile axioms of the instance graph."""
        return self._intraAxioms

    @property
    def interAxioms(self):
        """Return the interprofile axioms of the instance graph."""
        return self._interAxioms

    @property
    def instances(self):
        """Return the set of instances (hyper-edges) of the instance graph."""
        return self._instances

    def addInstances(self, instances: Set[Instance]):
        """Store new instances."""
        self._instances.update(instances)
    
    def isHeuristic(self):
        """Return True iff for this graph we are using the heuristic strategies."""
        return self._heuristics

    def profile2node(self, profile: AbstractProfile):
        """Given a profile, return its corresponding (unique) Node-object.

        Having a unique Node object is useful, as some persistant information is stored in the nodes."""
        try:
            return self._p2n[profile]
        # If the node does not exist, we create it.
        except KeyError:
            node = self.Node(self, profile)
            self._p2n[profile] = node
            return node

    def BFS(self, startProfile: AbstractProfile, depth: int=None) -> Iterator:
        """Run BFS from a profile over the graph.

            The BFS is implemented as an iterator. For each iteration `i`, it yields the set of instances that can be generated
            within a distance of `i` from the starting profile. For example:

                for instances in graph.BFS(profile):
                    # ...do something...
                    break

            Will "do something" over all instances that can be generated within a distance of 0 from the starting profile.

            Parameters
            ----------
            startProfile : AbstractProfile
                The profile from where we start the exploration.
            depth : int
                Maximum depth possible. Default: None (no constraint)

            Returns
            -------
            Iterator
                An iterator over sets of instances.
        """

        startNode = self.profile2node(startProfile)
        # Set the depth of the starting node to 0, and the current depth to -1.
        # The current depth is used to monitor everytime we explore all nodes within a distance `d` from the starting profile. Check the inner loop to see how it works!
        startNode.depth, currentDepth = 0, -1
        # The fifo contains the nodes that we reached, but still have to explore (or expand).
        self._fifo = deque()
        self._fifo.append(startNode)

        # While we still have nodes to explore in the queue.
        # Note that, for every profile in the queue, all of its mentioning intra-profile axiom instances have already been generated. (They are generated as the Node object is created.)
        while self._fifo:
            currentNode = self._fifo.popleft()
            # Set the current node as explored.
            currentNode.setExplored()

            # TODO: explain better how the currentDepth thing is used with examples

            # If we cross the maximum current depth, it means that we have reached a new "layer" of nodes (a new distance from the starting node).
            # Hence, we yield these instances, and then resume the execution. We also update the current depth.
            if currentNode.depth > currentDepth:
                currentDepth = currentNode.depth
                yield self.instances
            # If we have reached the maximum depth, we are done. 
            if currentDepth == depth:
                return

            # Now, we expand the node. When this happens, we generate all inter-profile instances mentioning this node.
            # While doing so, we reach all nodes connected to this profile, and hence generate their intra-profile instances.

            for axiom in self.interAxioms:

                # If the graph uses the heuristics, we ask the axiom to generate the instances using heuristics. Note that this requires passing the heuristic information to the axiom.
                if self.isHeuristic():
                    instances = axiom.getInstancesMentioningHeuristic(currentNode.profile, currentNode.getHeuristicInfo())
                else:
                    instances = axiom.getInstancesMentioning(currentNode.profile)

                # Register the axiom creating the instances.
                for instance in instances:
                    instance.created_by = axiom

                # Add the generated instances to the internal state.
                self.addInstances(instances)
                # For every new instance, we iterate over its mentioned profiles.
                for instance in instances:
                    for profile in instance.mentions():
                        # For each profile, we get the (unique) corresponding node.
                        node = self.profile2node(profile)
                        # We store the current axioms to the axiom whose instances connect said node.
                        node.setReachedBy(axiom)
                        # If this node was not explored yet, we add it to the queue, and set its depth.
                        if not node.isExplored():
                            node.depth = currentNode.depth + 1
                            self._fifo.append(node)

        # If we have exhausted the queue, return the instances one final time.
        yield self.instances