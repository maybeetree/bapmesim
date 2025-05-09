"""
meteorshower.py -- model resilience to meteor shower

This is a sample script bundled with bapmesim_tk.
It simulates how the mesh network degrades as nodes
are destroyed by falling meteors.
"""

nodes_active = []
nodes_total = []

scatter(num=200, loc=(-0.5, -0.5), scale=1)
scatter(num=100, loc=(0.5, 0.5), scale=2)

self.sim.make_graph(0.7)
nodes_active.append(self.sim.num_nodes)
nodes_total.append(self.sim.num_connected)

for _ in range(0, 10):

    meteors(size=0.5, num=10)

    self.sim.make_graph(0.7)
    nodes_active.append(self.sim.num_nodes)
    nodes_total.append(self.sim.num_connected)

fig, ax = plt.subplots(1)
ax.scatter(range(len(nodes_active)), nodes_active, label="Active Nodes")
ax.scatter(range(len(nodes_total)), nodes_total, label="Total Nodes")
ax.set_xlabel('Time')
ax.set_ylabel('Number of nodes')
ax.legend()
fig.show()

