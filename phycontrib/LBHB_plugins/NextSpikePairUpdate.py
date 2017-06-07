"""NextSpikePairUpdate output plugin.

This plugin adds a shortcut to the trace view to skip through spike pairs
organized by ISI.

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['NexpSpikePairUpdate']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Jan 2017
"""

import numpy as np
from phy import IPlugin
from phy.gui import Actions

class NextSpikePairUpdate(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_gui_ready(gui,**kwargs):

            actions = Actions(gui)            
            def go_to_spike_pair(increment):
                max_num=1000
                tv = gui.get_view('TraceView')
                m = controller.model
                cluster_ids = controller.supervisor.selected
                if len(cluster_ids) == 0:
                    return
                elif len(cluster_ids) == 1:
                    is_self=True
                else:
                    is_self=False
                try:
                    do_compute = self.current_clusters != cluster_ids
                except:
                    do_compute=True
                if do_compute:
                    print('computing spike pairs...')
                    spc = controller.supervisor.clustering.spikes_per_cluster
                    spike_ids = spc[cluster_ids[0]]
                    spike_times1 = m.spike_times[spike_ids]              
                    if is_self:
                        diffs=np.diff(spike_times1)
                    else:
                         spike_ids = spc[cluster_ids[1]]
                         spike_times2 = m.spike_times[spike_ids]
                         diffs=np.repeat(spike_times1[:,None],spike_times2.shape,axis=1)-np.repeat(spike_times2[:,None],spike_times1.shape,axis=1).T
                    self.max_num=np.min((np.prod(diffs.shape),max_num))
                    self.order=np.argsort(np.absolute(diffs),axis=None)[:self.max_num]                    
                    if is_self:
                        self.times=(spike_times1[self.order]+spike_times1[self.order+1])/2
                    else:
                        indexes = np.unravel_index(self.order,diffs.shape)
                        self.times=(spike_times1[indexes[0]]+spike_times2[indexes[1]])/2
                    self.current_index=0
                    self.current_clusters=cluster_ids
                    print('done')
                else:
                    self.current_index += increment
                if self.current_index == max_num:
                    self.current_index=0
                elif self.current_index < 0:
                    self.current_index=self.max_num-1
                tv.go_to(self.times[self.current_index])
                
                
            @actions.add(shortcut='alt+shift+pgdown',menu='TraceView')
            def go_to_next_spike_pair():
                go_to_spike_pair(1)

            @actions.add(shortcut='alt+shift+pgup',menu='TraceView')
            def go_to_previous_spike_pair():
                go_to_spike_pair(-1)

