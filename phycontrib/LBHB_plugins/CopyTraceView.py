"""CopyTraceView output plugin.

This plugin adds a shortcut to the trace view to skip through spike pairs
organized by ISI.

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['NexpSpikePairUpdate']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Jan 2017
"""

from phy import IPlugin
from phy.gui import Actions
from phy.cluster.views import TraceView

class CopyTraceView(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_gui_ready(gui,**kwargs):

            actions = Actions(gui) 
            @actions.add(menu='TraceView')
            def CopyTraceView():
                tv = gui.get_view('TraceView')
                m = controller.model                
                tv2 = TraceView(traces=tv.traces,
                      n_channels=tv.n_channels,
                      sample_rate=tv.sample_rate,
                      duration=tv.duration,
                      channel_vertical_order=m.channel_vertical_order,
                      )
                gui.add_view(tv2, name='Trace2View')
                tv2.do_show_labels = tv.do_show_labels
                tv2.set_interval(tv._interval)
                tv2.go_to(tv.time)
                tv2.panzoom.set_pan_zoom(zoom=tv.panzoom._zoom,pan=tv.panzoom._pan)
#                cluster_ids = controller.supervisor.selected
#                if len(cluster_ids) == 0:
#                    return
#                elif len(cluster_ids) == 1:
#                    is_self=True
#                else:
#                    is_self=False
#                try:
#                    do_compute = self.current_clusters != cluster_ids
#                except:
#                    do_compute=True
#                if do_compute:
#                    print('computing spike pairs...')
#                    spc = controller.supervisor.clustering.spikes_per_cluster
#                    spike_ids = spc[cluster_ids[0]]
#                    spike_times1 = m.spike_times[spike_ids]              
#                    if is_self:
#                        diffs=np.diff(spike_times1)
#                    else:
#                         spike_ids = spc[cluster_ids[1]]
#                         spike_times2 = m.spike_times[spike_ids]
#                         diffs=np.repeat(spike_times1[:,None],spike_times2.shape,axis=1)-np.repeat(spike_times2[:,None],spike_times1.shape,axis=1).T
#                    self.max_num=np.min((np.prod(diffs.shape),max_num))
#                    self.order=np.argsort(np.absolute(diffs),axis=None)[:self.max_num]                    
#                    if is_self:
#                        self.times=(spike_times1[self.order]+spike_times1[self.order+1])/2
#                    else:
#                        indexes = np.unravel_index(self.order,diffs.shape)
#                        self.times=(spike_times1[indexes[0]]+spike_times2[indexes[1]])/2
#                    self.current_index=0
#                    self.current_clusters=cluster_ids
#                    print('done')
#                else:
#                    self.current_index += increment
#                if self.current_index == max_num:
#                    self.current_index=0
#                elif self.current_index < 0:
#                    self.current_index=self.max_num-1
#                tv.go_to(self.times[self.current_index])

