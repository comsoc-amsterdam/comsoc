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

        pngs, outcomes, labels, profiles = {}, {}, {}, {}

        steps = nx.get_edge_attributes(self.tree, 'step')

        g = graphviz.Digraph('G')
        g.attr('node', shape='circle', label="", width="0.25")
        g.attr('edge', arrowsize=".5")
        g.attr(rankdir='LR')
        g.attr(bgcolor="#fefbd8")
        g.attr(nodesep="0.25")
        g.attr(ranksep="0.25")

        for n in self.tree.nodes():
            g.node(n.id, URL=n.id)

        profile_texts = {}
        
        for e in self.tree.edges():
            n, m = e
            g.edge(n.id, m.id)
            
            labels[m] = steps[e]

        for n in self.tree.nodes():

            profiles[n] = sorted(n.getMentionedProfiles())

            for p in profiles[n]:
                if p not in profile_texts:
                    profile_texts[p] = str(self.encoding.decode(p))

            outcomes[n] = {}

            for s in n.statements:
                p = s.getProfile()
                if not p in outcomes[n]:
                    outcomes[n][p] = [s.getOutcome()]
                else:
                    outcomes[n][p].append(s.getOutcome())

            g.node(n.id, style="filled")

            pngs[n] = base64.b64encode(g.pipe(format = 'png')).decode('utf-8')

            g.node(n.id, style="solid")
        
        sorted_nodes = list(nx.topological_sort(self.tree))
        o, p = self.justification.outcome, self.encoding.encode_profile(self.justification.profile)
        labels[sorted_nodes[0]] = f"We are going to prove our goal by contradiction. That is, we will show that, if we assume that {o} is not the outcome for {p}, we will reach a contradiction (i.e., we will have a profile with no possible outcomes). For each profile involved in the justification, in the table below, we show the possible outcomes."
        labels[sorted_nodes[-1]] += " Contradiction!"

        cmap = g.pipe(format = 'cmapx').decode('utf-8')

        return pngs, cmap, outcomes, labels, profiles, profile_texts, sorted_nodes, p