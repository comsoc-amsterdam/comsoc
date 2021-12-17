# This should be part of its own module TODO
import networkx as nx
import re
from .node import *
from .edge import *
from .statement import *

class ProofTree():
    'Represent a proof tree using networkx'

    def __init__(self, answerSet="", encoding=None, fact2instance = None):
        if answerSet != "":
            self.answerSet = answerSet
            self.encoding = encoding
            self.fact2instance = fact2instance
        self.nodes = {}
        self.edges = {}
        self.proofTree = nx.DiGraph()

    def getTree(self):
        """Return the proof tree containing the nodes and edges currently in use."""

        for nodeID in self.nodes.keys():
            self.proofTree.add_node(self.nodes[nodeID])

        for edgeID in self.edges.keys():
            edge = self.edges[edgeID]
            self.proofTree.add_edge(edge.getSrc(), edge.getDest(),step=edge.getStep())

        return self.proofTree


    def addNode(self, id):
        """Add node id to the tree"""

        node = Node(id, self.encoding)
        self.nodes[id] = node

    def addStatement(self, id, statement):
        """Add statement to node id."""

        self.nodes[id].addStatement(statement)

    def getStatementsFromNode(self, id):
        """Return the set of statements used is node id."""

        return self.nodes[id].getStatements()

    def addEdge(self, src, dest):
        """Add the edge (src,dest) to the tree"""

        edge = Edge(self.nodes[src], self.nodes[dest])
        self.edges[(src,dest)] = edge

    def addStep(self, src, dest, step):
        """Link edge (src,dest) with a contrete step."""

        self.edges[(src,dest)].linkToStep(step)


    def getHighestID(self):
        """The node ID that is the highest (used for naming purposes)."""

        ids = [int(id) for id in self.nodes.keys()]

        return max(ids)

    ### Working with Answer Sets ###

    def getTreeFromAnswerSet(self):
        """Transform the self answer set to a tree."""

        self.retrieveNodesFromAnswerSet()
        self.retrieveStatementsFromAnswerSet()
        self.retrieveEdgesFromAnswerSet()
        self.retrieveStepsFromAnswerSet()

        for nodeID in self.nodes.keys():
            self.proofTree.add_node(self.nodes[nodeID])

        for edgeID in self.edges.keys():
            edge = self.edges[edgeID]
            self.proofTree.add_edge(edge.getSrc(), edge.getDest(),step=edge.getStep())

        return self.proofTree

    def retrieveNodesFromAnswerSet(self):
        """Extract nodes from answer set."""

        for nodeAtom in [str(atom) for atom in self.answerSet if "node" in str(atom)]:
            nodeNumber = nodeAtom.replace("node(",'')
            nodeNumber = nodeNumber.replace(")",'')
            node = Node(nodeNumber, self.encoding)
            self.nodes[nodeNumber] = node

    def retrieveStatementsFromAnswerSet(self):
        """Extract statements associated with each node."""

        for nodeID in self.nodes.keys():
            for statementAtom in [str(atom) for atom in self.answerSet if "statement(" + nodeID + "," in str(atom)]:
                statementAtom = statementAtom.replace("statement(", "")
                statementAtom = statementAtom.replace(")","")
                _, profile, outcome = tuple(statementAtom.split(","))

                statement = Statement(profile,\
                    '{}' if outcome == 'oEmpty' else self.encoding.decode(outcome))
                self.nodes[nodeID].addStatement(statement)

    def retrieveEdgesFromAnswerSet(self):
        """Extract edges from answer set."""

        for edgeAtom in [str(atom) for atom in self.answerSet if "edge" in str(atom)]:
            src,dest = tuple(re.findall(r'\d+', edgeAtom))
            edge = Edge(self.nodes[src], self.nodes[dest])
            self.edges[(src,dest)] = edge

    def retrieveStepsFromAnswerSet(self):
        """Extract the steps of the proof associated with each edge."""

        for stepAtom in [str(atom) for atom in self.answerSet if "step" in str(atom)]:
            stepAtom = stepAtom[5:-1]  # remove step(...)
            fact = re.findall('.+\(.+\)', stepAtom)[0]  # get the fact
            head = re.findall('[^\(]+', fact)[0]  # get fact head
            arguments = fact[:-1].replace(head + '(', '').split(',')  # get the arguments
            src, dst = stepAtom.replace(fact + ',', '').split(',')

            edge = self.edges[(src, dst)]

            if head == 'intro':
                step = f"Consider profile {arguments[0]}: {self.encoding.decode(arguments[0])}."
            elif head == 'branching':
                profile, outcome, direction = arguments
                if direction == 'left':
                    step = f"Case: Let us assume that {self.encoding.decode(outcome)} is the outcome for {profile}."
                else:
                    step = f"Case: Let us assume that {self.encoding.decode(outcome)} is NOT the outcome for {profile}."
            else:   
                try :
                    step = self.fact2instance[fact].from_asp(fact, self.encoding)
                except KeyError:
                    step = fact
            
            edge.linkToStep(step)