import graphviz
import base64
import networkx as nx

import pathlib
from jinja2 import Environment, FileSystemLoader

import pickle

class DrawingWebsite():
    'Handle the drawing of a proof tree as dynamic document.'

    def __init__(self, prettified_tree, tree, justification, encoding, html):
        # Prettified tree: A networkx tree where the edges/nodes labels are in HTML. Will
        # be used to display the webpage.
        self.prettified_tree = prettified_tree
        # Tree: a networkx tree where the edges/nodes are in plain text. Will be sent in as feedback.
        self.tree = tree
        # Encoding: ASP encoding of objects.
        self.encoding = encoding
        # The justification object.
        self.justification = justification
        # A standalone html file describing the justification (will be sent in as feedback).
        self.html = html


        # Prepare jinja template for the tables
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

        """ This function returns a dictionary that encodes all the parameters necessary to render
        a jinja template for displaying a justification. """

        # get the steps (edge labels)
        steps = nx.get_edge_attributes(self.prettified_tree, 'step')
        labels = {}

        ## Clean graph (remove unused contradictions in the last step, prettify labels for contradictions)
        
        removable_nodes = set()  # nodes that are not useful
        is_there_a_contradiction = False  # whether this is a justification by contradiction or not

        # For every edge
        for e in self.prettified_tree.edges():
            n, m = e
            
            # The label of this node is the step that took us here (For example, an application of some axiom)
            labels[m] = steps[e]

            if m not in removable_nodes:  # we don't care about the labels of this nodes
                # Get the children of this node
                neighs = list(self.prettified_tree.neighbors(m))

                # If it is only one child, AND
                if len(neighs) == 1:
                    child = neighs[0]
                    # the only child is a leaf,
                    if not list(self.prettified_tree.neighbors(child)):
                        # We check whether we can cut this leaf, and rewrite the proof
                        # without contradictions. This happens if in the CURRENT node
                        # we already have only one possible outcome for the goal profile (the target outcome).
                        goal_statements = set()
                        # So, for the statements in this node that...
                        for s in m.statements:
                            # ...that regard the goal profile (always encoded as p0),
                            # add them
                            if s.getProfile() == 'p0':
                                goal_statements.add(s.getOutcome())

                        # If there is only the target outcome for the given profile
                        if goal_statements == {self.justification.outcome}:
                            removable_nodes.add(child)  # the leaf node is a trivial contradiction: we don't need it.
                elif len(neighs) == 0:  # no children: we are in a leaf, here a contradiction happens
                    labels[m] += " We're out of possible outcomes: contradiction!"
                    is_there_a_contradiction = True

        # Remove the useless nodes
        for node in removable_nodes:
            self.prettified_tree.remove_node(node)

        ### Build graph

        # Graphviz: we build a small graph png image used to navigate the tree
        g = graphviz.Digraph('G')
        g.attr('node', shape='circle', label="", width="0.25")
        g.attr('edge', arrowsize=".5")
        g.attr(rankdir='LR') # display it horizontally
        g.attr(nodesep="0.25")
        g.attr(ranksep="0.25")

        # add to the graph-png image the nodes. Why do we add the URL?
        # because the nodes in the PNG image will be clickable, and to make them clickable
        # we need an URL to identify them.
        for n in self.prettified_tree.nodes():
            g.node(n.id, URL=n.id)

        # Also add the edges
        for e in self.prettified_tree.edges():
            n, m = e
            g.edge(n.id, m.id)

        # prepare datastructs
        pngs, outcomes, profile_texts, profiles = {}, {}, {}, {}

        # For every node (step in the proof), we prepare the necessary data to display it
        for n in self.prettified_tree.nodes():

            # This structure contains the profile mentioned in this node
            profiles[n] = sorted(map(lambda p: self.encoding.prettify_profile(p), n.getMentionedProfiles()))

            # For each of these profiles, if we didn't already,
            # we save a pretty HTML description of it.
            for p in n.getMentionedProfiles():
                pretty_p = self.encoding.prettify_profile(p) # this is the html name of the profile (p1 becomes <i>R</i><sub>1</sub>)
                if pretty_p not in profile_texts:
                    profile_texts[pretty_p] = self.encoding.decode(p).prettify()

            # register, for this node, a dictionary mapping (the html name of) a profile to the list of its possible outcomes
            outcomes[n] = {}
            for s in n.statements:
                p = s.getProfile()
                pretty_p = self.encoding.prettify_profile(p)
                if not pretty_p in outcomes[n]:
                    outcomes[n][pretty_p] = [s.getOutcome()]
                else:
                    outcomes[n][pretty_p].append(s.getOutcome())

            # temporarily declare this node as filled in the graph (we highlight it)
            g.node(n.id, style="filled")

            # this dictionary maps each node to a png image where the current node is highlighted
            # further, the image is encoded in base64, this makes it easier to send it to the jinja template
            pngs[n] = base64.b64encode(g.pipe(format = 'png')).decode('utf-8')

            # de-highlight the node
            g.node(n.id, style="solid")
        
        # topological sort of the nodes (useful to traverse the proof tree linearly)
        sorted_nodes = list(nx.topological_sort(self.prettified_tree))
        # Target outcome and (html name of) the goal profile
        target_outcome = self.justification.outcome
        p = self.encoding.encode_profile(self.justification.profile, prettify = True)

        # Set the first label (basically, what the user sees in the landing page of the justification)
        # If this is a proof by contradiction (we decided this earlier)
        if is_there_a_contradiction:
            labels[sorted_nodes[0]] = f"We will show that if we assume that {target_outcome.prettify()} is <i>not</i> the outcome for {p}, we will reach a contradiction (i.e., we will have a profile with no possible outcomes). For each profile involved in the justification, in the table below, we show the possible outcomes."
        else:
            labels[sorted_nodes[0]] = f"We are going to show that {target_outcome.prettify()} must be the outcome for {p}. For each profile involved in the justification, in the table below, we show the possible outcomes."

        # Click-map for the png images (to make them clickable)
        # since all png images are equal (they just differ on the highlighted nodes),
        # the click-map is the same for each one
        cmap = g.pipe(format = 'cmapx').decode('utf-8')

        # Set of all possible outcomes (sorted by length first, and alphabetically on ties)
        all_outcomes = sorted(self.justification.scenario.outcomes, key = lambda out: (len(out), str(out)))
        # dictionary that maps every node to an HTML table that describes the outcomes available for every profile
        tables = self._make_tables(sorted_nodes, all_outcomes, profiles, profile_texts, outcomes, target_outcome)

        # The justification and its networkx justification tree (the plain-text, non-html version) are pickled
        # this will be sent in as feedback
        pickled_just = pickle.dumps({"justification": self.justification, "tree": self.tree})

        # Encode the feedback-data in base64, so we can store them into the webpage and send them in as feedback
        html_encoded = base64.b64encode(self.html.encode()).decode()
        justif_encoded = base64.b64encode(pickled_just).decode()

        # The complete data. Each key/value pair is a parameter/argument pair in the jinja template.
        # Check the justification.html template in the webapp to see how these things will be used.
        return {"len_nodes": len(sorted_nodes), "outcomes": outcomes,\
            "labels":labels, "profiles": profiles, "nodes": sorted_nodes, "pngs": pngs,\
            "map":cmap, "all_outcomes":all_outcomes, "tables":tables, "justification_html":html_encoded,\
            "justification_pickle":justif_encoded}