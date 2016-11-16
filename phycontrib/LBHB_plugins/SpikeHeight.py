"""SpikeHeight metric plugin.

This plugin adds a column to the metrics showing the spike height.

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['SpikeHeight']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Nov 2015
adapted from custom_stats.py example
"""

from phy import IPlugin


class SpikeHeight(IPlugin):
    def attach_to_controller(self, controller):
        """This method is called when a controller is created.

        The controller emits a few events:

        * `init()`: when the controller is created
        * `create_gui(gui)`: when the controller creates a GUI
        * `add_view(gui, view)`: when a view is added to a GUI

        You can register callback functions to these events.

        """

        # The controller defines several objects for the GUI.

        # The ManualClustering instance is responsible for the manual
        # clustering logic and the cluster views.
        mc = controller.manual_clustering

        # The context provides `cache()` and `memcache()` methods to cache
        # functions on disk or in memory, respectively.
        ctx = controller.context

        # We add a column in the cluster view and set it as the default.
        @mc.add_column(default=True)
        # We memcache it.
        @ctx.memcache
        def height(cluster_id):
            # This function takes a cluster id as input and returns a scalar.
            # data.data is a (n_spikes, n_samples, n_channels) array.
            data = controller.get_waveforms(cluster_id)[0]
            #(n_spikes, n_samples, n_channels)
            m=data.data.max()
            m=abs(data.data.min())
            m=abs(data.data.mean(0).min()) # mean over selected spikes, min over all samples and channels
            print('Cluster {:d} has shape {}, metric is {:.2f}'.format(cluster_id,data.data.shape,m))
            return m
