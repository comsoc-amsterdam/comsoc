from .drawingstatic import *
from .drawingdynamic import *

import matplotlib.pyplot as plt

import sys

class DisplayTreeInterface():
    'Interface class used to handle the display of a proof tree'

    def __init__(self, tree, mode="static"):
        self.tree = tree
        self.drawer = None
        self.mode = mode

    def exportTree(self, dest):
        "Export the tree to a file located at dest."

        if self.mode == "dynamic":
            self.drawer = DrawingDynamic(self.tree)
            return self.exportDynamic(dest)
        elif self.mode == "static":
            self.drawer = DrawingStatic(self.tree)
            self.exportStatic(dest)
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

        return html
