"""Interspike interval view plugin.

This plugin adds an interactive matplotlib figure showing the ISI histograms of
the selected clusters.

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['ISIView']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Nov 2015
"""

from phy import IPlugin
import numpy as np
import matplotlib.pyplot as plt
from phy.utils._color import _spike_colors

class ISIView(IPlugin):
    def attach_to_controller(self, controller):

        # Create the figure when initializing the GUI.
        plt.rc('xtick', color='w')        
        plt.rc('ytick', color='w')
        plt.rc('axes', edgecolor='w')
        f, ax = plt.subplots()
        rect = f.patch
        rect.set_facecolor('k')
        ax.set_axis_bgcolor('k')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')
        ax.get_yaxis().set_tick_params(direction='out')
        ax.get_xaxis().set_tick_params(direction='out')
        
        @controller.connect
        def on_create_gui(gui):
            # Called when the GUI is created.

            # We add the matplotlib figure to the GUI.
            gui.add_view(f, name='ISI')

            # We connect this function to the "select" event triggered
            # by the GUI at every cluster selection change.
            @gui.connect_
            def on_select(clusters):
                # We clear the figure.

                ax.clear()
                colors = _spike_colors(np.arange(len(clusters)))
                binsize=.1
                binmax=10
                bins=np.arange(0,binmax,binsize)
                for i in range(len(clusters)):
                    if len(clusters) == 1 :
                        colors[i][3]=1
                    spikes = 1000*controller.spike_times[controller.spike_clusters == clusters[i]]
                    ax.hist(np.diff(spikes), bins, edgecolor = 'none', facecolor = colors[i])
                ymin, ymax = ax.get_ylim()
                ax.vlines(1,ymin,ymax,colors='w',linestyles='dashed')
                # We update the figure.
                f.canvas.draw()
