# BAPMESIM: BachelorAfstudeerProject Mesh Networking Simulations

![Screenshot of `bapmesim_tk`](img/bapmesim_tk.png)

This repo contains our group's mesh networking simulations.
Currently there is only one, `bapmesim_tk`.

## Installing

Download and run the windows or linux build from the
[releases page](https://github.com/maybeetree/bapmesim/releases).

## Developing

You can install it with the standard Python method:

```sh
git clone https://github.com/maybeetree/bapmesim
pip install -e bapmesim
```

Once installed, you can run it as a module:

```sh
python3 -m bapmesim_tk
```

Note that `tkinter` is required.
If it is not already installed (it is usually bundled with Python),
check your package manager
for something like `python3-tkinter` or `python-tk`.


## Using

Use the scatter scatter tool (first from top) to place down clusters of nodes.
The meteor tool (second from top) simulates a meteor strike
that kills nodes in a specified range.
The meteors tool (third) simulates multiple meteor strikes
distributed evenly across the area covered by the nodes.
The plot tool (fourth) can be used to generate
a pie chard showing how many nodes are connected,
and a histogram showing the path length to the root node.
The script tool (fifth) can be used to run scripts.

## Scripting

In addition to the GUI, BAPMESIM also shows an interactive python
console that can be used to run python commands as well as BAPMESIM tools.
The script tool can also be used to load and execute a `.py` script file.

