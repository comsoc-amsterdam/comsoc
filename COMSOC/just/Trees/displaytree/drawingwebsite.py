import graphviz
import base64
import networkx as nx

import pathlib
from jinja2 import Environment, FileSystemLoader

import pickle

class DrawingWebsite():
    'Handle the drawing of a proof tree as dynamic document.'

    def __init__(self, prettified_tree, tree, justification, encoding, html):
        self.prettified_tree = prettified_tree
        self.tree = tree
        self.encoding = encoding
        self.justification = justification
        self.html = html

        self.templates_path = str(pathlib.Path(__file__).parent.resolve()) + '/templates'
        templateLoader = FileSystemLoader(self.templates_path)
        templateEnv = Environment(loader=templateLoader)
        self.tables_template = templateEnv.get_template('tables.html')

    # Function that, for a set of nodes (in a proof tree) and other auxiliary information,
    # returns a dictionary mapping a node to an HTML table that describes it.
    def _make_tables(self, nodes, all_outcomes, mentioned_profiles, profile_texts, mentioned_outcomes, target_outcome):

        """

            args:
            ----

            nodes: an iterator over the nodes of a tree.
            all_outcomes: iterator over all possible outcomes.
            mentioned_profiles: dictionary from a node to the profiles it mentions.
            profile_texts: dictionary from ALL profiles to a a pretty text representation
            mentioned_outcomes: dictionary from a node to a set of dictionaries from
                each (mentioned) profile to its available outcomes. Contains the special string `{}` if no outcome is possible
            target_outcome: the outcome to justify.
        """
        
        # Preliminary data

        pretty_outcomes = []  # links each outcome to an html string that represents is
        for outcome in all_outcomes:
            # outcome.prettify() sets all alternatives in italics
            # then, we remove the curly brackes, and instaed of a comma-separated list
            # have an endline separated list.
            pretty_outcomes.append(outcome.prettify().replace('{', '').replace('}', '').replace(', ', '<br>'))

        # all_profiles is a list of all the profiles.
        # we sort it alphabetically (pretty) and then set the
        # goal profile <i>R</i><sup>*</sup> as the first one
        # (by removing it and then attaching it in the head)
        all_profiles = sorted(profile_texts.keys())
        all_profiles.remove('<i>R</i><sup>*</sup>')
        all_profiles = ['<i>R</i><sup>*</sup>'] + all_profiles

        # Now, we build the actual tables
        tables = {}  # initialise final dictionary

        # For every node, construct the table:
        for node in nodes:
            # First, we obtain a set of all profiles (mentioned in this node) that have no possible outcomes (they will be colored in red).
            # This happens whenever the special token `{}` is in the mentioned outcomes. 
            contradictions = {profile for profile in mentioned_profiles[node] if "{}" in mentioned_outcomes[node][profile]}

            greenify = False  # flag: do we need to paint the goal profile in green in this node? (Happens whenever only the target outcome is available)
            if all_profiles[0] in mentioned_profiles[node]:  # if goal profile (recall that above we set it as the first one in this list) is mentioned
                # And there is exactly one available outcome, that is the target outcome
                if len(mentioned_outcomes[node][all_profiles[0]]) == 1 and target_outcome in mentioned_outcomes[node][all_profiles[0]]:
                    # Then we do paint it green!
                    greenify = True

            # The tables are instantiated from a template which uses all the information mentioned above
            tables[node] = self.tables_template.render(all_outcomes=all_outcomes,\
                current_profiles=mentioned_profiles[node], node=node, outcomes=mentioned_outcomes[node], contradictions=contradictions,\
                pretty_outcomes=pretty_outcomes, pretty_profiles=profile_texts,\
                all_profiles = all_profiles, greenify = greenify)

            # Finally, since we will save this inside a javascript variable, we replace every \n with spaces (effectively making this a one-liner)
            # and escape the quotes.
            tables[node] = tables[node].replace('\n', '   ').replace("\"", "\\\"")

        return tables

    def getContent(self):

        steps = nx.get_edge_attributes(self.prettified_tree, 'step')

        labels = {}

        ## Clean graph (remove unused contradictions, prettify labels for contradictions)
        
        removable_nodes = set()
        is_there_a_contradiction = False
        for e in self.prettified_tree.edges():
            n, m = e
            
            labels[m] = steps[e]

            if m not in removable_nodes:  # we don't care about the labels of this nodes
                neighs = list(self.prettified_tree.neighbors(m))

                if len(neighs) == 1:
                    child = neighs[0]
                    if not list(self.prettified_tree.neighbors(child)):  # only child is a leaf.
                        goal_statements = set()
                        for s in m.statements:
                            if s.getProfile() == 'p0':
                                goal_statements.add(s.getOutcome())

                        # there is only the target outcome for the given profile
                        if goal_statements == {self.justification.outcome}:
                            removable_nodes.add(child)  # trivial contradiction
                elif len(neighs) == 0:  # empty list: leaf of a tree
                    labels[m] += " We're out of possible outcomes: contradiction!"
                    is_there_a_contradiction = True

        for node in removable_nodes:
            self.prettified_tree.remove_node(node)

        ### Build graph

        g = graphviz.Digraph('G')
        g.attr('node', shape='circle', label="", width="0.25")
        g.attr('edge', arrowsize=".5")
        g.attr(rankdir='LR')
        g.attr(nodesep="0.25")
        g.attr(ranksep="0.25")

        for n in self.prettified_tree.nodes():
            g.node(n.id, URL=n.id)

        for e in self.prettified_tree.edges():
            n, m = e
            g.edge(n.id, m.id)

        pngs, outcomes, profile_texts, profiles = {}, {}, {}, {}

        for n in self.prettified_tree.nodes():

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
        
        sorted_nodes = list(nx.topological_sort(self.prettified_tree))
        target_outcome, p = self.justification.outcome, self.encoding.encode_profile(self.justification.profile, prettify = True)
        if is_there_a_contradiction:
            labels[sorted_nodes[0]] = f"We will show that if we assume that {target_outcome.prettify()} is <i>not</i> the outcome for {p}, we will reach a contradiction (i.e., we will have a profile with no possible outcomes). For each profile involved in the justification, in the table below, we show the possible outcomes."
        else:
            labels[sorted_nodes[0]] = f"We are going to show that {target_outcome.prettify()} must be the outcome for {p}. For each profile involved in the justification, in the table below, we show the possible outcomes."

        cmap = g.pipe(format = 'cmapx').decode('utf-8')

        all_outcomes = sorted(self.justification.scenario.outcomes, key = lambda out: (len(out), str(out)))
        tables = self._make_tables(sorted_nodes, all_outcomes, profiles, profile_texts, outcomes, target_outcome)

        pickled_just = pickle.dumps({"justification": self.justification, "tree": self.tree})

        html_encoded = base64.b64encode(self.html.encode()).decode()
        justif_encoded = base64.b64encode(pickled_just).decode()

        return {"len_nodes": len(sorted_nodes), "outcomes": outcomes,\
            "labels":labels, "profiles": profiles, "nodes": sorted_nodes, "pngs": pngs,\
            "map":cmap, "all_outcomes":all_outcomes, "tables":tables, "html_justification":html_encoded,\
            "justification":justif_encoded}