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
        labels[sorted_nodes[0]] = f"We are going to prove our goal by contradiction. That is, we will show that, if we assume that {o.prettify()} is <i>not</i> the outcome for {p}, we will reach a contradiction (i.e., we will have a profile with no possible outcomes). For each profile involved in the justification, in the table below, we show the possible outcomes."
        labels[sorted_nodes[-1]] += " Contradiction!"

        cmap = g.pipe(format = 'cmapx').decode('utf-8')

        return pngs, cmap, outcomes, labels, profiles, profile_texts, sorted_nodes