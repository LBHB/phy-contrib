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
import csv
from phy import IPlugin

class ChannelExportUpdate(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_create_gui(gui):
            @gui.connect_
            def on_request_save(spike_clusters, groups, controller=controller):
            
                # Save the clusters.
                np.save(filenames['spike_clusters'], spike_clusters)
                # Save the cluster groups.
                import sys
                if sys.version_info[0] < 3:
                    file = open(filenames['cluster_groups'], 'wb')
                else:
                    file = open(filenames['cluster_groups'], 'w', newline='')
                with file as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerow(['cluster_id', 'group'])
                    writer.writerows([(cluster, groups[cluster])
                    for cluster in sorted(groups)])
                    
                cluster_ids=sorted(groups)
                best_channels = np.zeros(len(cluster_ids))
                for i in range(len(cluster_ids)):
                    best_channels[i]=controller.get_best_channel(cluster_ids[i])
                np.save('best_channels.npy',best_channels)
                                