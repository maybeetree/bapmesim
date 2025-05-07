import tkinter as tk
import code
import platform
import logging
import importlib.resources

import numpy as np
import scipy as sp
import networkx as nx
import matplotlib.pyplot as plt

from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

from .iters import duplets
from . import res
from .res import img

# ??? `exit` not available when running in pyinstaller???
from sys import exit

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def reverse_canvas_cpair(cpair):
    x = (cpair[0] - 200) / 50
    y = (cpair[1] - 200) / 50
    return x, y

BITMAP = """
#define im_width 32
#define im_height 32
static char im_bits[] = {
0xaf,0x6d,0xeb,0xd6,0x55,0xdb,0xb6,0x2f,
0xaf,0xaa,0x6a,0x6d,0x55,0x7b,0xd7,0x1b,
0xad,0xd6,0xb5,0xae,0xad,0x55,0x6f,0x05,
0xad,0xba,0xab,0xd6,0xaa,0xd5,0x5f,0x93,
0xad,0x76,0x7d,0x67,0x5a,0xd5,0xd7,0xa3,
0xad,0xbd,0xfe,0xea,0x5a,0xab,0x69,0xb3,
0xad,0x55,0xde,0xd8,0x2e,0x2b,0xb5,0x6a,
0x69,0x4b,0x3f,0xb4,0x9e,0x92,0xb5,0xed,
0xd5,0xca,0x9c,0xb4,0x5a,0xa1,0x2a,0x6d,
0xad,0x6c,0x5f,0xda,0x2c,0x91,0xbb,0xf6,
0xad,0xaa,0x96,0xaa,0x5a,0xca,0x9d,0xfe,
0x2c,0xa5,0x2a,0xd3,0x9a,0x8a,0x4f,0xfd,
0x2c,0x25,0x4a,0x6b,0x4d,0x45,0x9f,0xba,
0x1a,0xaa,0x7a,0xb5,0xaa,0x44,0x6b,0x5b,
0x1a,0x55,0xfd,0x5e,0x4e,0xa2,0x6b,0x59,
0x9a,0xa4,0xde,0x4a,0x4a,0xd2,0xf5,0xaa
};
"""

DO_NOT_GARBAGE_COLLECT = []

def get_bitmap(filename, master):
    bitmap = tk.BitmapImage(
        master=master,
        data=importlib.resources.read_text(res.img, filename)
        )
    DO_NOT_GARBAGE_COLLECT.append(bitmap)
    return bitmap

class Sim:
    """
    Simulator backend, no graphics.

    Attributes
    ----------

    nodes_pos
        np.array of coordinate pairs.
        This contains all nodes of all clusters.

    clst_indices
        Indices of `self.nodes_pos` that point to the
        clusterhead of every cluster.
        The last item is not an index, but the total
        number of nodes.

    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.nodes_pos = None
        self.clst_indices = [0]

    def scatter_nodes(self, num, loc, scale):
        scattered_nodes = np.random.normal(
            loc=loc,
            scale=scale,
            size=(num - 1, 2)
            )

        if self.nodes_pos is None:
            self.nodes_pos = np.vstack((
                    loc,
                    scattered_nodes
                    ))

        else:
            self.nodes_pos = np.vstack((
                    self.nodes_pos,
                    loc,
                    scattered_nodes
                    ))

        self.clst_indices.append(len(self.nodes_pos))

        self.make_tree()

    @property
    def num_nodes(self):
        return len(self.nodes_pos)

    @property
    def num_connected(self):
        return len(self.path_lengths)

    @property
    def num_disconnected(self):
        return self.num_nodes - self.num_connected

    def make_tree(self):
        self.kdtree = sp.spatial.KDTree(self.nodes_pos)

    def make_graph(self, node_range):
        self.graph = nx.Graph()
        self.graph.add_nodes_from(range(self.num_nodes))

        self.graph.add_edges_from(
            self.kdtree.query_pairs(node_range)
            )

        self.path_lengths = nx.single_source_shortest_path_length(
            self.graph, 0
            )

class SimCMD:
    """Interactive commands for simulation."""
    def __init__(self, simtk):
        self.simtk = simtk

    def scatter(self, num, loc=(0, 0), scale=1):
        self.simtk.sim.scatter_nodes(num, loc, scale)
        self.simtk.draw_nodes()

    def asteroid(self, size, loc=(0, 0)):
        points = self.simtk.sim.kdtree.query_ball_point(loc, size)
        #points.sort()
        print(points)
        print(len(points))

        # FIXME cleanup this spaghett
        print(f"brefore: {self.simtk.sim.clst_indices}")
        nodes_in_clsts = [0] * len(self.simtk.sim.clst_indices)
        for point in points:
            for i, (left, right) in enumerate(duplets(self.simtk.sim.clst_indices)):
                i = i + 1
                if left <= point < right:
                    print(f"point {point} in {right}")
                    for x in range(i, len(self.simtk.sim.clst_indices)):
                        nodes_in_clsts[x] += 1

        for i, x in enumerate(nodes_in_clsts):
            self.simtk.sim.clst_indices[i] -= x

        #self.simtk.sim.clst_indices[-1] -= len(points)
        print(f"after: {self.simtk.sim.clst_indices}")

        print(len(self.simtk.sim.nodes_pos))
        self.simtk.sim.nodes_pos = np.delete(
            self.simtk.sim.nodes_pos, points, axis=0)
        print(len(self.simtk.sim.nodes_pos))
        self.simtk.sim.make_tree()
        self.simtk.draw_nodes()

    def make_plots(self, node_range=0.1):
        self.simtk.sim.make_graph(node_range)
        self.simtk.plot_path_length_hist()
        self.simtk.plot_connected_pie()

class Toolbar:
    def __init__(self, frame_tbar, frame_opts, canvas, cmd, root):
        self.frame_tbar = frame_tbar
        self.frame_opts = frame_opts
        self.canvas = canvas
        self.cmd = cmd
        self.root = root

        self.buts = []
        self.tools = []
        self.frames = []
        self.tool = None
    
    def add_tool(self, tool):
        but = tk.Button(
            self.frame_tbar,
            text=tool.name,
            image=get_bitmap(tool.icon, self.root),
            command=lambda tool_num=len(self.tools): self.activate(tool_num)
            )

        frame = tk.Frame(self.frame_opts)

        self.root.bind(
            f'<Alt-{tool.hotkey}>',
            lambda event, tool_num=len(self.tools): self.activate(tool_num)
            )

        self.tools.append(tool(frame, self.canvas, self.cmd))
        self.buts.append(but)
        self.frames.append(frame)

        but.pack()

    def activate(self, tool_num):
        if self.tool is not None:
            self.frames[self.tool].pack_forget()
        self.tool = tool_num
        self.frames[self.tool].pack()

        children = self.frames[self.tool].winfo_children()
        if children:
            first_child = children[0]
            first_child.focus_set()

            if isinstance(first_child, tk.Spinbox):
                # Select all text in spinbox
                first_child.selection_adjust(999999)

    def cb_click(self, event):
        self.tools[self.tool].cb_click(event)

class Tool:
    def __init__(self, frame, canvas, cmd):
        self.frame = frame
        self.canvas = canvas
        self.cmd = cmd

        self.setup()

    def cb_click(self):
        pass

class ToolScatter(Tool):
    name = "Scatter Nodes"
    icon = "scatter.xbm"
    hotkey = 's'

    def setup(self):
        self.ui_num = tk.Spinbox(
            self.frame,
            value=100,
            width=5,
            )

        self.ui_scale = tk.Spinbox(
            self.frame,
            value=1,
            width=5,
            )

        #tk.Label(self.root, text="Number of nodes:").grid(row=2, column=0)

        tk.Label(self.frame, text="Number of nodes:").grid(row=0, column=0)
        self.ui_num.grid(row=0, column=1)
        tk.Label(self.frame, text="Scale:").grid(row=0, column=2)
        self.ui_scale.grid(row=0, column=3)

    def cb_click(self, event):
        x, y = reverse_canvas_cpair((event.x, event.y))
        self.cmd.scatter(
            num=int(self.ui_num.get()),
            loc=(x, y),
            scale=float(self.ui_scale.get())
            )

class ToolAsteroid(Tool):
    name = "Asteroid"
    icon = "asteroid.xbm"
    hotkey = 'a'

    def setup(self):
        self.ui_size = tk.Spinbox(
            self.frame,
            value=0.5
            )

        #tk.Label(self.root, text="Number of nodes:").grid(row=2, column=0)
        self.ui_size.grid(row=0, column=1)

    def cb_click(self, event):
        x, y = reverse_canvas_cpair((event.x, event.y))
        self.cmd.asteroid(
            size=float(self.ui_size.get()),
            loc=(x, y),
            )

class ToolPlot(Tool):
    name = "Plot"
    icon = "plot.xbm"
    hotkey = 'p'

    def setup(self):
        self.ui_range = tk.Spinbox(
            self.frame,
            value=0.7
            )
        self.ui_but = tk.Button(
            self.frame,
            text="Make plots!",
            command=self.make_plots
            )
        self.ui_range.pack()
        self.ui_but.pack()

    def make_plots(self):
        self.cmd.make_plots(node_range=float(self.ui_range.get()))

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


        self.frame_tbar = tk.Frame(self.root)


        self.frame_tbar.grid(row=0, column=0, rowspan=3)
        self.canvas.grid(row=0, column=1, columnspan=2, rowspan=3)
        self.frame_opts = tk.Frame(self.root)
        self.frame_opts.grid(row=2, column=1, columnspan=2)

        self.canvas_pie.get_tk_widget().grid(row=0, column=3) 
        self.canvas_hist.get_tk_widget().grid(row=1, column=3) 

        self.cmd = SimCMD(self)

        self.tbar = Toolbar(
            self.frame_tbar,
            self.frame_opts,
            self.canvas,
            self.cmd,
            self.root,
            )
        self.tbar.add_tool(ToolScatter)
        self.tbar.add_tool(ToolAsteroid)
        self.tbar.add_tool(ToolPlot)

        self.canvas.bind("<Button-1>", self.tbar.cb_click)

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
        locs = {
            **locals(),
            **globals(),
            **{
                k: v for k in dir(self.cmd)
                if not k.startswith('_')
                and callable(v := getattr(self.cmd, k))
                }
            }
        code.interact(local=locs)

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





