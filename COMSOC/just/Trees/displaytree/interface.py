from .drawingstatic import *
from .drawingdynamic import *
from .drawingwebsite import *

import matplotlib.pyplot as plt

import sys

class DisplayTreeInterface():
    'Interface class used to handle the display of a proof tree'

    def __init__(self, tree, justification, mode="static", encoding = None):
        self.tree = tree
        self.drawer = None
        self.mode = mode
        self.encoding = encoding
        self.justification = justification

    def exportTree(self, dest):
        "Export the tree to a file located at dest."

        if self.mode == "dynamic":
            self.drawer = DrawingDynamic(self.tree, self.justification)
            if dest is None:
                return self.exportDynamic(dest)
            else:
                self.exportDynamic(dest)
        elif self.mode == "static":
            self.drawer = DrawingStatic(self.tree)
            self.exportStatic(dest)
        elif self.mode == "website":
            self.drawer = DrawingWebsite(self.tree, self.justification, self.encoding)
            return self.drawer.drawTree()
        else:
            sys.exit("Drawing mode unknown!")


    def exportStatic(self, dest):
        """Export the tree to a static picture located at dest."""
        assert self.drawer != None, "No drawer defined!"

        plt.figure(1,figsize=(13,13))
        self.drawer.drawTree()
        plt.savefig(dest, dpi=300)
        plt.clf()

    def exportDynamic(self, dest):
        """Export the tree as a dynamic document located at dest. If dest=None, return the html instead."""
        assert self.drawer != None, "No drawer defined!"

        html = self.drawer.getContent()

        if dest is not None:
            with open(dest, "w") as file:
                file.write(html)
        else:
            return html
