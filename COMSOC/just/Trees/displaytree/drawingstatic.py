
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout

class DrawingStatic():
    'Handle the drawing of a proof tree as static picture.'

    def __init__(self, tree):
        self.tree = tree
        self.pos = graphviz_layout(self.tree, prog="dot")


    def drawTree(self):
        """Draw the proof tree."""

        self.drawNodes()
        self.drawEdges()


    def drawNodes(self):
        """Draw the nodes of the proof tree."""

        labels = {node: node.getLabel() for node in self.tree.nodes}

        nx.draw_networkx_labels(self.tree, self.pos, labels, font_size=5)
        nx.draw_networkx_nodes(self.tree, self.pos, node_size=0)

    def drawEdges(self):
        """Draw the edges of the proof tree."""

        step = nx.get_edge_attributes(self.tree,'step')
        labels = {edge: step[edge] for edge in self.tree.edges}

        nx.draw_networkx_edge_labels(self.tree, self.pos, edge_labels=labels, font_size=5, rotate=False)
        nx.draw_networkx_edges(self.tree, self.pos, width=0.5)
