import tkinter as tk
import code
import platform

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

# ??? `exit` not available when running in pyinstaller???
from sys import exit

def plot_hist_with_inf(ax, finite_data, inf_count, bin_width):
    """
    Plots a histogram on the given matplotlib Axes object, with an extra bin for np.inf values.
    
    Parameters:
        ax (matplotlib.axes.Axes): The Axes object to plot on.
        finite_data (array-like): Array of finite numeric values.
        inf_count (int): Number of np.inf values to include in an extra bin.
        bin_width (float): Width of each histogram bin for the finite data.
    """
    # Determine the range for the finite data
    min_val = np.min(finite_data)
    max_val = np.max(finite_data)

    # Create bin edges using the specified bin width
    bins = np.arange(min_val, max_val + bin_width, bin_width)

    # Add an extra bin edge for the infinity bin
    bins_with_inf = np.append(bins, bins[-1] + bin_width)

    # Compute histogram for finite values
    hist, _ = np.histogram(finite_data, bins=bins)

    # Add the inf count as an extra bin
    hist_with_inf = np.append(hist, inf_count)

    # Define bin labels
    labels = [f'{bins[i]:.2f}–{bins[i+1]:.2f}' for i in range(len(bins) - 1)]
    labels.append('inf')

    # Plot
    ax.bar(range(len(hist_with_inf)), hist_with_inf, align='center', tick_label=labels)
    ax.set_xlabel('Bins')
    ax.set_ylabel('Frequency')
    ax.set_title('Histogram with extra bin for infinity')
    ax.tick_params(axis='x', rotation=45)

class Sim:
    """Simulator, no graphics."""
    def __init__(self):
        pass

    def scatter_nodes(self, num_nodes):
        self.nodes_pos = np.vstack((
                ((0, 0), ),  # <-- this is the root node

                # And the bellow are the scattered nodes
                np.random.normal(
                    size=(num_nodes, 2)
                    )
                ))

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
        for i in range(self.num_nodes):
            for j in range(i, self.num_nodes):
                # FIXME slow and dumb
                if np.linalg.norm(self.nodes_pos[i] - self.nodes_pos[j]) <= node_range:
                    self.graph.add_edge(i, j)
                    self.graph.add_edge(j, i)

        #self.paths2root = nx.shortest_path(self.graph, 0).keys()
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

        if cpair[0] == 0 and cpair[1] == 0:
            style['fill'] = 'red'

        self.canvas.create_line(cx - 2, cy - 2, cx + 2, cy + 2, **style)
        self.canvas.create_line(cx - 2, cy + 2, cx + 2, cy - 2, **style)

    def draw_nodes(self):
        self.canvas.delete("all")
        for cpair in self.sim.nodes_pos:
            self.draw_node(cpair)

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





