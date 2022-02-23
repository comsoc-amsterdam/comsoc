from .drawingdynamic import *
from .drawingwebsite import *

class DisplayTreeInterface():
    """Interface class used to handle the display of a proof tree"""

    def __init__(self, proofTree, justification, source = "ASP", encoding = None):
        self.proofTree = proofTree
        self.drawer = None
        self.encoding = encoding
        self.justification = justification
        self.source = source

    def exportTree(self, display, dest = None):
        "Export the tree to a file located at dest."

        if display == "dynamic":
            return self.exportDynamic(dest)
        elif display == "website":
            return self.exportWebsite()
        else:
            raise NotImplementedError("Drawing mode unknown!")            

    def exportDynamic(self, dest = None):
        """Export the tree as a dynamic document located at dest. If dest=None, return the html instead."""

        if self.source == "ASP":
            tree = self.proofTree.getTreeFromAnswerSet(prettify = False)
        else:
            raise NotImplementedError("Only ASP trees have been implemented")

        html = DrawingDynamic(tree, self.justification).getContent()

        if dest is not None:
            with open(dest, "w") as file:
                file.write(html)
        
        return html

    def exportWebsite(self):
        if self.source == "ASP":
            tree = self.proofTree.getTreeFromAnswerSet(prettify = False)  # this creates a tree where the labels are in plaintext
            prettified_tree = self.proofTree.getTreeFromAnswerSet(prettify = True) # this creates a tree where the labels are in HTML
        else:
            raise NotImplementedError("Only ASP trees have been implemented")

        # First, create the stand-alone html justification. This is actually used in the web presentation itself.
        html = self.exportDynamic()

        # prepare the website drawer
        self.drawer = DrawingWebsite(prettified_tree, tree, self.justification, self.encoding, html)

        # get the content
        return self.drawer.getContent()
