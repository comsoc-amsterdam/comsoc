import graphviz
import base64
import networkx as nx

class DrawingWebsite():
    'Handle the drawing of a proof tree as dynamic document.'

    def __init__(self, tree, justification, encoding):
        self.tree = tree
        self.encoding = encoding
        self.justification = justification

    def drawTree(self):
        """Return the content of a file necessary to draw the proof tree."""

        steps = nx.get_edge_attributes(self.tree, 'step')

        labels = {}

        ## Clean graph (remove unused contradictions, prettify labels for contradictions)
        
        removable_nodes = set()
        is_there_a_contradiction = False
        for e in self.tree.edges():
            n, m = e
            
            labels[m] = steps[e]

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
                elif len(neighs) == 0:  # empty list: leaf of a tree
                    labels[m] += " We're out of possible outcomes: contradiction!"
                    is_there_a_contradiction = True

        for node in removable_nodes:
            self.tree.remove_node(node)

        ### Build graph

        g = graphviz.Digraph('G')
        g.attr('node', shape='circle', label="", width="0.25")
        g.attr('edge', arrowsize=".5")
        g.attr(rankdir='LR')
        g.attr(nodesep="0.25")
        g.attr(ranksep="0.25")

        for n in self.tree.nodes():
            g.node(n.id, URL=n.id)

        for e in self.tree.edges():
            n, m = e
            g.edge(n.id, m.id)


        pngs, outcomes, profile_texts, profiles = {}, {}, {}, {}

        for n in self.tree.nodes():

            profiles[n] = sorted(map(lambda p: self.encoding.prettify_profile(p), n.getMentionedProfiles()))

            for p in n.getMentionedProfiles():
                pretty_p = self.encoding.prettify_profile(p)
                if pretty_p not in profile_texts:
                    profile_texts[pretty_p] = self.encoding.decode(p).prettify()

            outcomes[n] = {}

            for s in n.statements:
                p = s.getProfile()
                pretty_p = self.encoding.prettify_profile(p)
                if not pretty_p in outcomes[n]:
                    outcomes[n][pretty_p] = [s.getOutcome()]
                else:
                    outcomes[n][pretty_p].append(s.getOutcome())

            g.node(n.id, style="filled")

            pngs[n] = base64.b64encode(g.pipe(format = 'png')).decode('utf-8')

            g.node(n.id, style="solid")
        
        sorted_nodes = list(nx.topological_sort(self.tree))
        o, p = self.justification.outcome, self.encoding.encode_profile(self.justification.profile, prettify = True)
        if is_there_a_contradiction:
            labels[sorted_nodes[0]] = f"We will show that if we assume that {o.prettify()} is <i>not</i> the outcome for {p}, we will reach a contradiction (i.e., we will have a profile with no possible outcomes). For each profile involved in the justification, in the table below, we show the possible outcomes."
        else:
            labels[sorted_nodes[0]] = f"We are going to show that {o.prettify()} must be the outcome for {p}. For each profile involved in the justification, in the table below, we show the possible outcomes."

        cmap = g.pipe(format = 'cmapx').decode('utf-8')

        return pngs, cmap, outcomes, labels, profiles, profile_texts, sorted_nodes, o