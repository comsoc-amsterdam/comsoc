
import networkx as nx
from jinja2 import Environment, FileSystemLoader


class DrawingDynamic():
    'Handle the drawing of a proof tree as dynamic document.'

    def __init__(self, tree):
        self.tree = tree
        
        templateLoader = FileSystemLoader('./COMSOC/just/Trees/displaytree/templates')
        templateEnv = Environment(loader=templateLoader)
        self.template = templateEnv.get_template('tree.html')


    def getContent(self):
        """Return the content of a file necessary to draw the proof tree."""

        nodeLabels = {node: node.getLabel() for node in self.tree.nodes()}

        step = nx.get_edge_attributes(self.tree, 'step')
        edgeLabels = {edge: step[edge] for edge in self.tree.edges()}

        return self.template.render(nodes=self.tree.nodes(), edges=self.tree.edges(), nodeLabels=nodeLabels, edgeLabels=edgeLabels)
