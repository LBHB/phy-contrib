"""Feature template projection vs time view plugin.

This plugin adds an interactive vispy figure showing the projection of selected 
spikes onto the templatre of the first cluster vs time

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['FeatureTemplateTimeView']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Jan 2017
"""

from phy import IPlugin
from phy.utils import Bunch
import numpy as np
import matplotlib.pyplot as plt
from vispy import visuals as vis
from vispy.app import Canvas
from phy.plot import View
from phy.utils._color import _spike_colors, ColorSelector, _colormap
from phy.cluster.manual.views import (select_traces, ScatterView)

class FeatureTemplateTime(ScatterView):
    pass

class FeatureTemplateTimeView(IPlugin):
    def get_template_projections(self,cluster_ids):
        if len(cluster_ids) < 1 :
            return None

        ni = self.controller.get_cluster_templates(cluster_ids[0])
        x_min=np.inf
        x_max=-np.inf
        y_min=np.inf
        y_max=-np.inf
        out=list()
        for cid in cluster_ids:
            si = self.controller._select_spikes(cid, self.controller.n_spikes_features)
            ti = self.controller._get_template_features(si)
            x  = self.controller.spike_times[si]
            y  = np.average(ti, weights=ni, axis=1)
            # Compute the data bounds.
            x_min = min(x.min(), x_min)
            y_min = min(y.min(), y_min)
            x_max = max(x.max(), x_max)
            y_max = max(y.max(), y_max)
            out.append(Bunch(x=x, y=y, spike_ids=si))
        data_bounds = (x_min, y_min, x_max, y_max)
        for i in range(len(out)):
            out[i].data_bounds=data_bounds

        return out
                
    def attach_to_controller(self, controller):
        self.controller=controller
        # Create the figure when initializing the GUI.
        @controller.connect
        def on_create_gui(gui):
            # Called when the GUI is created.
            view = FeatureTemplateTime(coords=self.get_template_projections)
#            @gui.connect_
#            def on_select(clusters):
#                
#                with view.building():
#                    #view.scatter(x, y, color=c, size=s, marker='square')
#                    colors = _spike_colors(np.arange(len(clusters)))      
#                    
#                    for i in range(len(clusters)):
#                        coords=controller.get_amplitudes(clusters[i])                   
#                        view[0].scatter(x=coords.x,y=coords.y, 
#                                    color=colors[i], 
#                                    size=3, 
#                                    marker='disc',
#                                    )
#                        #sp=view[1].hist(coords.y,color=(1,0,0,1),100)
#                        ah=vis.HistogramVisual(coords.y,bins=100,color=(1,0,0,1),orientation='v') #how to add this to view[1] ??
#                view.show()
            controller._add_view(gui,view)
            #gui.add_view(view, name='AmplitudeViewWithHistogram')

