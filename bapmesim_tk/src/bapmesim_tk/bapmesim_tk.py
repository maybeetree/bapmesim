import tkinter as tk
import code
import platform
import logging

import numpy as np
import scipy as sp
import networkx as nx
import matplotlib.pyplot as plt

from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

from .iters import duplets

# ??? `exit` not available when running in pyinstaller???
from sys import exit

log = logging.getLogger(__name__)

class Sim:
    """
    Simulator backend, no graphics.

    Attributes
    ----------

    nodes_pos
        np.array of coordinate pairs.
        This contains all nodes of all clusters.

    cluster_indices
        Indices of `self.nodes_pos` that point to the
        clusterhead of every cluster.
        The last item is not an index, but the total
        number of nodes.

    """
    def __init__(self):
        self.nodes_pos = None
        self.clst_indices = [0, 0]
        pass

    def scatter_nodes(self, num_nodes, clusterhead_pos=(0, 0)):
        scattered_nodes = np.random.normal(
            size=(num_nodes - 1, 2)
            )

        if self.nodes_pos is None:
            self.nodes_pos = np.vstack((
                    clusterhead_pos,
                    scattered_nodes
                    ))

        else:
            self.nodes_pos = np.vstack((
                    self.nodes_pos,
                    clusterhead_pos,
                    scattered_nodes
                    ))

        self.clst_indices.pop()
        self.clst_indices.append(len(self.nodes_pos) - num_nodes)
        self.clst_indices.append(len(self.nodes_pos))

    @property
    def num_nodes(self):
        return len(self.nodes_pos)

    @property
    def num_connected(self):
        return len(self.path_lengths)

    @property
    def num_disconnected(self):
        return self.num_nodes - self.num_connected

    def make_graph(self, node_range):
        self.graph = nx.Graph()
        self.graph.add_nodes_from(range(self.num_nodes))

        self.kdtree = sp.spatial.KDTree(self.nodes_pos)
        self.graph.add_edges_from(
            self.kdtree.query_pairs(node_range)
            )

        self.path_lengths = nx.single_source_shortest_path_length(
            self.graph, 0
            )


class SimTK:
    """Simulator with TK graphics. Encapsulates `Sim` instance."""
    def __init__(self, sim: Sim):
        self.sim = sim

        self.fig_pie, self.ax_pie = plt.subplots(1, figsize=(3.5, 2.5))
        self.fig_hist, self.ax_hist = plt.subplots(1, figsize=(3.5, 2.5))

        self.root = tk.Tk()

        if platform.system() == 'Linux':
            self.root.attributes('-type', 'dialog')
            # Tell tiling WMs to spawn the window in floating mode.
            # This will actually crash on Windows, so have
            # to check the platform first.

        # Exit program on window close
        # (i.e. kill interactive shell if it is running)
        self.root.protocol("WM_DELETE_WINDOW", exit)

        self.canvas = tk.Canvas(
            self.root,
            width=400,
            height=400
            )

        self.canvas_pie = FigureCanvasTkAgg(
            self.fig_pie,
            self.root,
            )

        self.canvas_hist = FigureCanvasTkAgg(
            self.fig_hist,
            self.root,
            )

        self.but_scatter = tk.Button(
            self.root,
            text="Scatter nodes",
            command=self.callback_scatter
            )

        self.spin_num_nodes = tk.Spinbox(
            self.root,
            value=100
            )

        self.but_plots = tk.Button(
            self.root,
            text="Make plots",
            command=self.callback_plots
            )

        self.spin_node_range = tk.Spinbox(
            self.root,
            value=0.6
            )

        self.canvas.grid(row=0, column=0, columnspan=3, rowspan=2)

        tk.Label(self.root, text="Number of nodes:").grid(row=2, column=0)
        self.spin_num_nodes.grid(row=2, column=1)
        self.but_scatter.grid(row=2, column=2)

        tk.Label(self.root, text="Node range:").grid(row=3, column=0)
        self.spin_node_range.grid(row=3, column=1)
        self.but_plots.grid(row=3, column=2)

        self.canvas_pie.get_tk_widget().grid(row=0, column=3) 
        self.canvas_hist.get_tk_widget().grid(row=1, column=3) 

    def callback_plots(self):
        self.sim.make_graph(float(self.spin_node_range.get()))
        self.plot_path_length_hist()
        self.plot_connected_pie()

    def callback_scatter(self):
        self.sim.scatter_nodes(int(self.spin_num_nodes.get()))
        self.draw_nodes()

    def canvas_cpair(self, cpair):
        cx = cpair[0] * 50 + 200
        cy = cpair[1] * 50 + 200
        return cx, cy

    def draw_node(self, cpair, style=None):
        #x, y = self.sim.nodes_pos[index]
        cx, cy = self.canvas_cpair(cpair)

        style = style or {}

        self.canvas.create_line(cx - 2, cy - 2, cx + 2, cy + 2, **style)
        self.canvas.create_line(cx - 2, cy + 2, cx + 2, cy - 2, **style)

    def draw_nodes(self):
        self.canvas.delete("all")

        for clst, clst_next in duplets(self.sim.clst_indices):

            if clst_next - clst > 200:
                log.info(f"Drawing 200 nodes of {clst_next - clst}")

            for node_i in range(clst, min(clst + 200, clst_next)):
                self.draw_node(self.sim.nodes_pos[node_i])

    def plot_path_length_hist(self):
        """Make plot of number of hops to root node for each node."""
        self.ax_hist.clear()
        self.ax_hist.hist(
            self.sim.path_lengths.values(),
            bins=tuple(range(
                0,
                max(self.sim.path_lengths.values()) + 2
                ))
            )
        self.canvas_hist.draw()

    def plot_connected_pie(self):
        self.ax_pie.clear()
        self.ax_pie.pie(
            (self.sim.num_connected, self.sim.num_disconnected),
            labels=('connected', 'disconnected'),
            )
        #self.ax_pie.legend()
        self.canvas_pie.draw()

    def mainloop(self):
        self.root.mainloop()

    def spawn_shell(self):
        code.interact(local={**locals(), **globals()})

    def spawn_shell_nonblocking(self):
        self.root.after(1, self.spawn_shell)

def cli():
    sim = Sim()
    #sim.scatter_nodes(100)
    #sim.make_graph(0.6)

    simtk = SimTK(sim)
    #simtk.draw_nodes()
    #simtk.plot_path_length_hist()
    #simtk.plot_connected_pie()

    simtk.spawn_shell_nonblocking()
    simtk.mainloop()





