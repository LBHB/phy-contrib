"""Interspike interval view plugin.

This plugin adds a matplotlib figure showing the ISI histograms of
the selected clusters.

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['ISIView']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Nov 2016
"""

from phy import IPlugin
import numpy as np
#import matplotlib
#matplotlib.use("Qt4Agg")
import matplotlib.pyplot as plt
from phy.utils._color import _spike_colors

class ISIView(IPlugin):
    def attach_to_controller(self, controller):
            
        @controller.connect
        def on_gui_ready(gui,**kwargs):
            # Called when the GUI is created.

            # Create the figure when initializing the GUI.
            plt.rc('xtick', color='w')        
            plt.rc('ytick', color='w')
            plt.rc('axes', edgecolor='w')
            
            f = plt.figure()
            ax = f.add_axes([0.15, 0.1, 0.78, 0.87])
            rect = f.patch
            rect.set_facecolor('k')
            ax.set_axis_bgcolor('k')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.yaxis.set_ticks_position('left')
            ax.xaxis.set_ticks_position('bottom')
            ax.get_yaxis().set_tick_params(direction='out')
            ax.get_xaxis().set_tick_params(direction='out')
            binsize=.1
            binmax=10
            bins=np.arange(0,binmax,binsize)     
                #        hist,bin_edges=np.histogram(np.zeros(1), bins=bins)
    #        colors = _spike_colors(np.arange(1))
    #        h1=ax.bar(bin_edges[:-1], hist, width = 1, edgecolor = 'None', facecolor = colors[0])
    #        f.canvas.draw()

            # We add the matplotlib figure to the GUI.
            gui.add_view(f, name='ISI')

            # We connect this function to the "select" event triggered
            # by the GUI at every cluster selection change.
            @gui.connect_
            def on_select(clusters,tf=f,tax=ax,bins=bins,**kwargs):
                # We clear the figure.
                tax.clear()
                colors = _spike_colors(np.arange(len(clusters)))

                for i in range(len(clusters)):
                    if len(clusters) == 1 :
                        colors[i][3]=1
                    spikes = 1000*controller.model.spike_times[controller.model.spike_clusters == clusters[i]]
                    #hist,bin_edges=np.histogram(np.diff(spikes), bins=bins)
                    #ax.bar(bin_edges[:-1], hist, width = 1, edgecolor = 'None', facecolor = colors[i])
                    #ax.plot(bin_edges[:-1], hist, color = colors[i])
                    #ax.plot([0, 1], [0, 1], color='r')
                    
                    tax.hist(np.diff(spikes), bins, edgecolor = 'None', facecolor = colors[i])
                ymin, ymax = tax.get_ylim()
                tax.vlines(1,ymin,ymax,colors='w',linestyles='dashed')
                # We update the figure.
                
                tf.canvas.draw()
