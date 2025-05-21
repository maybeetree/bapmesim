import tkinter as tk
import tkinter.filedialog
import platform
import logging
import importlib.resources

import numpy as np
import scipy as sp
import networkx as nx
import matplotlib.pyplot as plt
import rasterio

from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

from .iters import duplets
from . import res
from . import sample_scripts
from . import sample_terrains
from .res import img

# ??? `exit` not available when running in pyinstaller???
from sys import exit

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


try:
    import IPython
    import threading
    from IPython.core.debugger import set_trace
    HAVE_IPYTHON=True
except ImportError:
    log.error(
        "Could not import IPython. Falling back to "
        "builtin `code.InteractiveConsole`. "
        "Expect jank."
        )
    import code
    HAVE_IPYTHON=False


def reverse_canvas_cpair(cpair):
    x = (cpair[0] - 200) / 50
    y = (cpair[1] - 200) / 50
    return x, y

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

    def load_terrain(self, *args):
        self.ter_reader = rasterio.open(*args)
        self.ter = self.ter_reader.read(1)

class SimCMD:
    """Interactive commands for simulation."""
    def __init__(self, simtk):
        self.simtk = simtk

    def scatter(self, num, loc=(0, 0), scale=1):
        self.simtk.sim.scatter_nodes(num, loc, scale)
        self.simtk.draw_nodes()

    def meteor(self, size, loc=(0, 0)):
        points = self.simtk.sim.kdtree.query_ball_point(loc, size)
        #points.sort()
        #print(points)
        #print(len(points))

        # FIXME cleanup this spaghett
        #print(f"brefore: {self.simtk.sim.clst_indices}")
        nodes_in_clsts = [0] * len(self.simtk.sim.clst_indices)
        for point in points:
            for i, (left, right) in enumerate(duplets(self.simtk.sim.clst_indices)):
                i = i + 1
                if left <= point < right:
                    #print(f"point {point} in {right}")
                    for x in range(i, len(self.simtk.sim.clst_indices)):
                        nodes_in_clsts[x] += 1

        for i, x in enumerate(nodes_in_clsts):
            self.simtk.sim.clst_indices[i] -= x

        #self.simtk.sim.clst_indices[-1] -= len(points)
        #print(f"after: {self.simtk.sim.clst_indices}")

        #print(len(self.simtk.sim.nodes_pos))
        self.simtk.sim.nodes_pos = np.delete(
            self.simtk.sim.nodes_pos, points, axis=0)
        #print(len(self.simtk.sim.nodes_pos))
        self.simtk.sim.make_tree()
        self.simtk.draw_nodes()

    def meteors(self, size, num):
        xmin, ymin = self.simtk.sim.nodes_pos.min(axis=0)
        xmax, ymax = self.simtk.sim.nodes_pos.max(axis=0)
        positions = np.random.uniform(
            [xmin, ymin],
            [xmax, ymax],
            size=[num, 2]
            )
        for loc in positions:
            self.meteor(size, loc)

    def make_plots(self, node_range=0.1):
        self.simtk.sim.make_graph(node_range)
        self.simtk.plot_path_length_hist()
        self.simtk.plot_connected_pie()

    def egg(self):
        self.simtk.egg()

    def load_terrain(self, path):
        self.simtk.sim.load_terrain(path)
        self.simtk.show_terrain()

    def hillshade(self, azi: float, alti: float):
        # Thanks to
        # https://www.neonscience.org/resources/learning-hub/tutorials/create-hillshade-py
        azi = np.deg2rad(360.0 - azi)
        alti = np.deg2rad(alti)

        x, y = np.gradient(self.simtk.sim.ter)
        slope = np.pi / 2. - np.arctan(np.sqrt(x * x + y * y))
        aspect = np.arctan2(-x, y)

        shaded = (
            np.sin(azi) * np.sin(slope)
            + np.cos(alti)
            * np.cos(slope)
            * np.cos((azi - np.pi / 2.) - aspect)
            )

        scale = np.iinfo(self.simtk.sim.ter.dtype).max

        self.simtk.sim.shaded = (
            scale * (shaded + 1) / 2 ).astype(self.simtk.sim.ter.dtype)
        self.simtk.show_terrain()

    def script(self, scriptpath, outpath):
        with open(scriptpath, 'r') as f:
            scriptcode = f.read()

        if HAVE_IPYTHON:
            exec(scriptcode, self.simtk.console_locs)
        else:
            self.simtk.console_code.runsource(
                scriptcode,
                symbol='exec'
                )


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

        self.counter = 1
    
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

        if self.tool == tool_num:
            self.counter += 1
        else:
            self.counter = 1
        if self.counter == 7:
            self.counter = 1
            self.cmd.egg()

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
        if self.tool is None:
            return
        self.tools[self.tool].cb_click(event)

class Tool:
    def __init__(self, frame, canvas, cmd):
        self.frame = frame
        self.canvas = canvas
        self.cmd = cmd

        self.setup()

    def cb_click(self, event):
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

class ToolMeteor(Tool):
    name = "Meteor"
    icon = "meteor.xbm"
    hotkey = 'm'

    def setup(self):
        self.ui_size = tk.Spinbox(
            self.frame,
            value=0.5
            )

        #tk.Label(self.root, text="Number of nodes:").grid(row=2, column=0)
        self.ui_size.grid(row=0, column=1)

    def cb_click(self, event):
        x, y = reverse_canvas_cpair((event.x, event.y))
        self.cmd.meteor(
            size=float(self.ui_size.get()),
            loc=(x, y),
            )

class ToolMeteors(Tool):
    name = "Meteors"
    icon = "meteors.xbm"
    hotkey = 'M'

    def setup(self):
        self.ui_size = tk.Spinbox(
            self.frame,
            value=0.5
            )
        self.ui_num = tk.Spinbox(
            self.frame,
            value=100
            )
        self.ui_but = tk.Button(
            self.frame,
            text="Blast!",
            command=lambda: self.cb_click(None)
            )

        tk.Label(self.frame, text="Meteor size:").grid(row=0, column=0)
        self.ui_size.grid(row=0, column=1)
        tk.Label(self.frame, text="Number of meteors:").grid(row=1, column=0)
        self.ui_num.grid(row=1, column=1)

        self.ui_but.grid(row=2, column=0, columnspan=2)

    def cb_click(self, event):
        self.cmd.meteors(
            size=float(self.ui_size.get()),
            num=int(self.ui_num.get()),
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

class ToolScripts(Tool):
    name = "Scripts"
    icon = "scripts.xbm"
    hotkey = 'c'

    def setup(self):
        self.ui_but_script = tk.Button(
            self.frame,
            text="Choose script",
            command=self.choose_script
            )
        self.ui_lab_script = tk.Label(
            self.frame,
            text="<not set>"
            )
        self.ui_but_output = tk.Button(
            self.frame,
            text="Choose output directory",
            command=self.choose_dir
            )
        self.ui_lab_output = tk.Label(
            self.frame,
            text="<not set>"
            )
        self.ui_but_run = tk.Button(
            self.frame,
            text="Run!",
            command=self.run
            )

        self.ui_but_script.grid(row=0, column=0)
        self.ui_lab_script.grid(row=0, column=1)
        #self.ui_but_output.grid(row=1, column=0)
        #self.ui_lab_output.grid(row=1, column=1)
        #self.ui_but_run.grid(row=2, column=0, columnspan=2)
        self.ui_but_run.grid(row=1, column=0, columnspan=2)

        self.scriptpath = None
        self.outpath = None

        self.update_button_state()

    def choose_script(self):
        # FIXME zipfile/etc. This is a context manager for a reason!
        with importlib.resources.path(sample_scripts, ".") as p:
            startpath = str(p)

        scriptpath = tk.filedialog.askopenfilename(
            initialdir = startpath,
            title = "Select Script",
            filetypes = (
                ("Python scripts", "*.py"),
                ("all files", "*")
                )
            )
        if not scriptpath:
            return

        self.scriptpath = scriptpath
        self.ui_lab_script.config(text=scriptpath)
        self.update_button_state()

    def choose_dir(self):
        outpath = tk.filedialog.askdirectory()
        if not outpath:
            return

        self.outpath = outpath
        self.ui_lab_output.config(text=outpath)
        self.update_button_state()

    def update_button_state(self):
        self.ui_but_run.config(
            state=(
                ["disabled", "normal"]
                [None not in {self.scriptpath, }]
                )
            )
        #self.ui_but_run.config(
        #    state=(
        #        ["disabled", "normal"]
        #        [None not in {self.outpath, self.scriptpath}]
        #        )
        #    )

    def run(self):
        self.cmd.script(self.scriptpath, self.outpath)

class ToolTerrain(Tool):
    name = "Terrain"
    icon = "terrain.xbm"
    hotkey = 't'

    def setup(self):
        self.ui_but = tk.Button(
            self.frame,
            text="Load terrain",
            command=self.load_terrain
            )
        self.ui_lab = tk.Label(
            self.frame,
            text="<not set>"
            )

        self.ui_but.grid(row=0, column=0)
        self.ui_lab.grid(row=1, column=0)

    def load_terrain(self):
        # FIXME zipfile/etc. This is a context manager for a reason!
        with importlib.resources.path(sample_terrains, ".") as p:
            startpath = str(p)

        path = tk.filedialog.askopenfilename(
            initialdir = startpath,
            title = "Select Terrain File",
            filetypes = (
                ("all files", "*"),
                )
            )
        if not path:
            return

        self.cmd.load_terrain(path)

class ToolHillshade(Tool):
    name = "Hillshade"
    icon = "hillshade.xbm"
    hotkey = 'h'

    def setup(self):
        self.ui_azi = tk.Scale(
            self.frame,
            from_=-180,
            to=180,
            orient="horizontal"
            )
        self.ui_alti = tk.Scale(
            self.frame,
            from_=-180,
            to=180,
            orient="horizontal"
            )
        self.ui_but = tk.Button(
            self.frame,
            text="Calculate!",
            command=self.hillshade
            )

        tk.Label(self.frame, text="Azimuth:").grid(row=0, column=0)
        self.ui_azi.grid(row=0, column=1)
        tk.Label(self.frame, text="Altitude:").grid(row=1, column=0)
        self.ui_alti.grid(row=1, column=1)
        
        self.ui_but.grid(row=3)

    def hillshade(self):
        self.cmd.hillshade(
            float(self.ui_azi.get()),
            float(self.ui_alti.get()),
            )


class SimTK:
    """Simulator with TK graphics. Encapsulates `Sim` instance."""
    def __init__(self, sim: Sim):
        self.sim = sim

        self.fig_pie, self.ax_pie = plt.subplots(1, figsize=(3.5, 2.5))
        self.fig_hist, self.ax_hist = plt.subplots(1, figsize=(3.5, 2.5))

        self.root = tk.Tk()

        self.scroll_x = 0
        self.scroll_y = 0

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
        self.tbar.add_tool(ToolMeteor)
        self.tbar.add_tool(ToolMeteors)
        self.tbar.add_tool(ToolPlot)
        self.tbar.add_tool(ToolTerrain)
        self.tbar.add_tool(ToolHillshade)
        self.tbar.add_tool(ToolScripts)

        self.canvas.bind("<Button>", self.cb_button)
        self.canvas.bind("<MouseWheel>", self.cb_mousewheel)

    def cb_button(self, event):
        if event.num == 1:
            self.tbar.cb_click(event)

        elif event.num == 2:
            pass

        # The below handles scrolling.
        # Vertical scrolling is buttons 4 and 5.
        # Horizontal scrolling *in xorg* is buttons 6 and 7
        # but tkinter doesn't actually support these
        # (I'm still testing for it just in case).
        #
        # What tkinter actually does if it
        # receives horizontal scroll events is it pretends
        # that they are also buttons 4 and 5 with the shift key pressed
        # down (event.state == 1).
        #
        # Testing for this also means that we automatically support
        # mouse users who have only vertical scroll and actually
        # hold down shift when they want to scroll horizontally
        #
        # Windows scroll handling works completely differently,
        # that's handled in cb_mousewheel

        elif event.num == 4 and event.state == 1 or event.num == 6:
            self.scroll_x += 1
            self.canvas.scan_dragto(self.scroll_x, self.scroll_y)

        elif event.num == 5 and event.state == 1 or event.num == 7:
            self.scroll_x -= 1
            self.canvas.scan_dragto(self.scroll_x, self.scroll_y)

        elif event.num == 4:
            self.scroll_y += 1
            self.canvas.scan_dragto(self.scroll_x, self.scroll_y)

        elif event.num == 5:
            self.scroll_y -= 1
            self.canvas.scan_dragto(self.scroll_x, self.scroll_y)

        # FIXME state is probably a bitmask,
        # read it idiomatically
        # TODO there are other scrolling methods,
        # integration with scrollbar widget. Are these better?
    
    def cb_mousewheel(self, event):
        # MouseWheel events are only emitted in Windows.
        # For linux/xorg scrolling is handled in cb_button
        if event.state == 1:
            self.scroll_x += event.delta // abs(event.delta)
        else:
            self.scroll_y += event.delta // abs(event.delta)
        self.canvas.scan_dragto(self.scroll_x, self.scroll_y)


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
        self.console_locs = {
            **locals(),
            **globals(),
            **{
                k: v for k in dir(self.cmd)
                if not k.startswith('_')
                and callable(v := getattr(self.cmd, k))
                }
            }

        if HAVE_IPYTHON:
            self.console_ipy = IPython.terminal.embed.InteractiveShellEmbed(
                #config=c,
                user_ns=self.console_locs
                )
            self.console_ipy()
        else:
            self.console_code = code.InteractiveConsole(
                locals=self.console_locs
                )
            self.console_code.interact()

    def spawn_shell_nonblocking(self):
        if HAVE_IPYTHON:
            threading.Thread(
                target=self.spawn_shell,
                daemon=True
                ).start()
        else:
            self.root.after(1, self.spawn_shell)

    def egg(self):
        win_egg = tk.Toplevel()
        if platform.system() == 'Linux':
            win_egg.attributes('-type', 'dialog')
        image = tk.PhotoImage(
            data=importlib.resources.read_binary(res.img, "informative.png"),
            master=win_egg
            ).zoom(8, 8)
        DO_NOT_GARBAGE_COLLECT.append(image)
        tk.Label(
            win_egg,
            image=image,
            ).grid(row=0, column=0, rowspan=2)
        informative = tk.Checkbutton(
            win_egg,
            text="Informative",
            )
        unfortunate = tk.Checkbutton(
            win_egg,
            text="Unfortunate",
            )

        informative.toggle()
        unfortunate.toggle()

        informative.grid(row=0, column=1)
        unfortunate.grid(row=1, column=1)

    def show_terrain(self):
        # FIXME this is some top-quality spaghett
        image = getattr(self.sim, 'shaded', self.sim.ter)

        height, width = image.shape
        info = np.iinfo(image.dtype)
        norm = image / (info.max - info.min) + (info.min / (info.max - info.min))
        uint8 = (norm * 255).astype(np.uint8)

        # Thanks https://stackoverflow.com/a/68601202
        # for this clever trick
        data = b''.join((
            f'P5 {width} {height} 255 '.encode('ascii'),
            uint8.tobytes()
            ))

        self.ter_img = tk.PhotoImage(
            master=self.root,
            width=width,
            height=height,
            data=data,
            format='PPM'
            )#.subsample(10, 10)
        #self.ter_img = tk.PhotoImage(
        #    file=path, master=self.root
        #    ).subsample(10, 10)
        self.canvas.create_image((width / 2, height / 2), image=self.ter_img)

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





