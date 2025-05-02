# BAPMESIM: BachelorAfstudeerProject Mesh Networking Simulations

![Screenshot of `bapmesim_tk`](img/bapmesim_tk.png)

This repo contains our group's mesh networking simulations.
Currently there is only one, `bapmesim_tk`.

## Using

Download and run the windows or linux build from the
[releases page](https://github.com/maybeetree/bapmesim/releases).

## Developing

You can install it with the standard Python method:

```sh
git clone https://github.com/maybeetree/bapmesim
pip install -e bapmesim/bapmesim_tk
```

Once installed, you can run it as a module:

```sh
python3 -m bapmesim_tk
```

Note that `tkinter` is required.
If it is not already installed (it is usually bundled with Python),
check your package manager
for something like `python3-tkinter` or `python-tk`.

