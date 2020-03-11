"""ChannelExportUpdate output plugin.

This plugin adds to phy's default save function to additionally create
a best_channels.npy file containing the phy best channels when you press save.

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['ChannelExportUpdate']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Nov 2016
"""

import numpy as np
from phy import IPlugin
import os.path as op
# spike_clusters, groups, labels,
class ChannelExportUpdate(IPlugin):

    def attach_to_controller(self, controller):
        @controller.connect
        def on_gui_ready(gui,**kwargs):
            @controller.supervisor.connect
            #def on_request_save(spike_clusters, groups, amplitude, contamination,
            #                    KS_label, labels, controller=controller):
            def on_request_save(*args, controller=controller):
                if len(args) >= 6:
                    spike_clusters = args[0]
                    groups = args[1]
                    amplitude = args[2]
                    contamination = args[3]
                    KS_label = args[4]
                    labels = args[5]
                elif len(args) == 3:
                    spike_clusters = args[0]
                    groups = args[1]
                    labels = args[2]
                else:
                    pass
                cluster_ids=sorted(groups)
                best_channels = np.zeros(len(cluster_ids))
                for i in range(len(cluster_ids)):
                    best_channels[i]=controller.get_best_channel(cluster_ids[i])
                np.save(op.join(controller.model.dir_path,'best_channels.npy'),best_channels)
