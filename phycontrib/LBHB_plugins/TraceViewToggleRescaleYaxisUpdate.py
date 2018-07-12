"""TraceViewToggleRescaleYaxisUpdate output plugin.


To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['TraceViewToggleRescaleYaxisUpdate']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Jan 2017
"""

import numpy as np
from phy import IPlugin
from phy.gui import Actions

class TraceViewToggleRescaleYaxisUpdate(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_add_view(gui,tv,**kwargs):

            from PyQt4.QtCore import pyqtRemoveInputHook
            from pdb import set_trace
            pyqtRemoveInputHook()
            set_trace()  
            @tv.connect
            def set_interval(self, interval=None, change_status=True,
                     force_update=False):
                """Display the traces and spikes in a given interval."""
                if interval is None:
                    interval = self._interval
                interval = self._restrict_interval(interval)
                if not force_update and interval == self._interval:
                    return
                self._interval = interval
                start, end = interval
                self.clear()
        
                # Set the status message.
                if change_status:
                    self.set_status('Interval: {:.3f} s - {:.3f} s'.format(start, end))
        
                # Load the traces.
                traces = self.traces(interval)
        
                # Find the data bounds.
                from PyQt4.QtCore import pyqtRemoveInputHook
                from pdb import set_trace
                pyqtRemoveInputHook()
                set_trace()  
                if self._rescale_yaxis or self._data_bounds is None:
                    ymin, ymax = traces.data.min(), traces.data.max()
                else:
                    ymin, ymax = self._data_bounds[1], self._data_bounds[3]
                data_bounds = (start, ymin, end, ymax)
                # Used for spike click.
                self._data_bounds = data_bounds
                self._waveform_times = []
        
                # Plot the traces.
                self._plot_traces(traces.data,
                                  color=traces.get('color', None),
                                  data_bounds=data_bounds,
                                  )
        
                # Plot the spikes.
                waveforms = traces.waveforms
                assert isinstance(waveforms, list)
                for w in waveforms:
                    self._plot_waveforms(waveforms=w.data,
                                         color=w.color,
                                         channel_ids=w.get('channel_ids', None),
                                         start_time=w.start_time,
                                         data_bounds=data_bounds,
                                         )
                    self._waveform_times.append((w.start_time,
                                                 w.spike_id,
                                                 w.spike_cluster,
                                                 w.get('channel_ids', None),
                                                 ))
        
                # Plot the labels.
                if self.do_show_labels:
                    self._plot_labels(traces.data, data_bounds=data_bounds)
        
                self.build()
                self.update()
                
                
            @tv.actions.add(shortcut='alt+r')
            def toggle_rescale_yaxis(tv):
                    self._rescale_yaxis = not self._rescale_yaxis
                    self.set_status('rescale_yaxis set to {}'.format(self._rescale_yaxis))

