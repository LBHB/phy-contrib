"""Custom view plugin.

This plugin adds an interactive matplotlib figure showing the ISI of the
first selected cluster.

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.KwikGUI.plugins = ['CustomView']
```

"""

from phy import IPlugin
import numpy as np
import matplotlib.pyplot as plt
from vispy import visuals as vis
from vispy.app import Canvas
from phy.plot import View
from phy.utils._color import _spike_colors, ColorSelector, _colormap

class AmplitudeViewWithHistogram(IPlugin):
    def attach_to_controller(self, controller):

        # Create the figure when initializing the GUI.
        @controller.connect
        def on_create_gui(gui):
            # Called when the GUI is created.
            box_pos=((1,1),(2,1))
            view = View(layout='boxed', box_pos=box_pos)
            
            @gui.connect_
            def on_select(clusters):
                
                with view.building():
                    #view.scatter(x, y, color=c, size=s, marker='square')
                    colors = _spike_colors(np.arange(len(clusters)))      
                    
                    for i in range(len(clusters)):
                        coords=controller.get_amplitudes(clusters[i])                   
                        view[0].scatter(x=coords.x,y=coords.y, 
                                    color=colors[i], 
                                    size=3, 
                                    marker='disc',
                                    )
                        #sp=view[1].hist(coords.y,color=(1,0,0,1),100)
                        ah=vis.HistogramVisual(coords.y,bins=100,color=(1,0,0,1),orientation='v') #how to add this to view[1] ??
                view.show()

            gui.add_view(view, name='AmplitudeViewWithHistogram')

