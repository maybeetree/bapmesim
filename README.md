# BAPMESIM: BachelorAfstudeerProject Mesh Networking Simulations

![Screenshot of `bapmesim_tk`](img/bapmesim_tk.png)

This repo contains our group's mesh networking simulations.
Currently there is only one, `bapmesim_tk`.

## Installing

Download and run the windows or linux build from the
[releases page](https://github.com/maybeetree/bapmesim/releases).


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

### Making your own builds

Our own binary builds are created using github actions
which run the windows and linux build scripts in the `scripts` directory.
If you would like to make binary builds yourself,
you can use these build scripts as a reference.
They will probably not work out of the box on your machine though,
you will need to edit them to fit your environment.

#### Using pyinstaller with virtiofs

If you're trying to debug the windows build process in a VM
and you're mounting this repository into the VM using virtiofs,
you will run an obscure error that sounds like
"volume does not have a recognised filesystem"
or something like that.

To fix it you need to perform the following incantation
(inside the VM) and reboot it:

```
reg add HKLM\Software\VirtIO-FS /v MountPoint /d \\.\Z:
```

More info:
<https://github.com/virtio-win/kvm-guest-drivers-windows/issues/517>

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

