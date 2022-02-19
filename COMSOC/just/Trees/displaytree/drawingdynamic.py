import pathlib
import networkx as nx
from jinja2 import Environment, FileSystemLoader


class DrawingDynamic():
    'Handle the drawing of a proof tree as dynamic document.'

    def __init__(self, tree, justification):
        self.tree = tree
        self.justification = justification
        
        self.templates_path = str(pathlib.Path(__file__).parent.resolve()) + '/templates'
        templateLoader = FileSystemLoader(self.templates_path)
        templateEnv = Environment(loader=templateLoader)
        self.template = templateEnv.get_template('tree.html')


    def getContent(self):
        """Return the content of a file necessary to draw the proof tree."""

        nodeLabels = {node: node.getLabel() for node in self.tree.nodes()}


        ## Clean graph (remove unused contradictions, prettify labels for contradictions)
        removable_nodes = set()
        for e in self.tree.edges():
            n, m = e
            
            if m not in removable_nodes:  # we don't care about the labels of this nodes
                neighs = list(self.tree.neighbors(m))

                if len(neighs) == 1:
                    child = neighs[0]
                    if not list(self.tree.neighbors(child)):  # only child is a leaf.
                        if len(m.statements) == 1:  # there is only one possible outcome
                            s = m.statements[0]
                            # there is only the target outcome for the given profile
                            if s.getProfile() == 'p0' and s.getOutcome() == self.justification.outcome:
                                removable_nodes.add(child)  # trivial contradiction

        for node in removable_nodes:
            self.tree.remove_node(node)

        ################

        step = nx.get_edge_attributes(self.tree, 'step')
        edgeLabels = {edge: step[edge] for edge in self.tree.edges()}

        return self.template.render(
                nodes=self.tree.nodes(), edges=self.tree.edges(),
                nodeLabels=nodeLabels, edgeLabels=edgeLabels)
