"""ChannelExportUpdate output plugin.

This plugin replaces phy's default svae function to additionally create
a best_channels.npy file containing the phy best channels.

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['ChannelExportUpdate']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Nov 2015
"""
filenames = {
    'spike_templates': 'spike_templates.npy',
    'spike_clusters': 'spike_clusters.npy',
    'cluster_groups': 'cluster_groups.csv',

    'spike_samples': 'spike_times.npy',
    'amplitudes': 'amplitudes.npy',
    'templates': 'templates.npy',
    'templates_unw': 'templates_unw.npy',

    'channel_mapping': 'channel_map.npy',
    'channel_positions': 'channel_positions.npy',
    'whitening_matrix': 'whitening_mat.npy',

    'features': 'pc_features.npy',
    'features_ind': 'pc_feature_ind.npy',
    'features_spike_ids': 'pc_feature_spike_ids.npy',

    'template_features': 'template_features.npy',
    'template_features_ind': 'template_feature_ind.npy',

    'similar_templates': 'similar_templates.npy',
}

import numpy as np
from phy import IPlugin
import os.path as op

class ChannelExportUpdate(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_create_gui(gui):
            @gui.connect_
            def on_request_save(spike_clusters, groups, controller=controller):
                                
                cluster_ids=sorted(groups)
                best_channels = np.zeros(len(cluster_ids))
                for i in range(len(cluster_ids)):
                    best_channels[i]=controller.get_best_channel(cluster_ids[i])
                np.save(op.join(controller.path,'best_channels.npy'),best_channels)
                                