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
check your package manager.

- Alpine Linux: `apk add python3-tkinter`
- Void Linux: `xbps-install -Syu python3-tkinter`


## Using

Use the scatter scatter tool (first from top) to place down clusters of nodes.
The meteor tool (second from top) simulates a meteor strike
that kills nodes in a specified range.
The meteors tool (third) simulates multiple meteor strikes
distributed evenly across the area covered by the nodes.
The plot tool (fourth) can be used to generate
a pie chart showing how many nodes are connected,
and a histogram showing the path length to the root node.
The script tool (fifth) can be used to run scripts.

## Scripting

In addition to the GUI, BAPMESIM also shows an interactive python
console that can be used to run python commands as well as BAPMESIM tools.
The script tool can also be used to load and execute a `.py` script file.

## License

`bapmesim_tk` is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, version 3 of the License only.

`bapmesim_tk` is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
`bapmesim_tk`. If not, see <https://www.gnu.org/licenses/>. 

---

Copyright (c) 2025, maybetree.

