"""ExportClusterWaveforms output plugin.

This plugin creates a npy file containing an array of the waveforms for 
the selected clusters cluster (N_channels,N_samples,N_clusters)

This plugin is called a s ansippet. To use it type ':' to get into snippet mode,
then type:
ecw
or 
ecw N
where N is the max number of waveforms per cluster to use (default 1000)
use a really high number to use all waveforms.


To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['ExportClusterWaveforms']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Nov 2016
"""

from phy.gui import Actions
import numpy as np
from phy import IPlugin

class ExportClusterWaveforms(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_create_gui(gui):
           
            
            actions = Actions(gui)
            @actions.add(alias='ecw')            
            def ExportClusterWaveforms(cluster_ids='all',max_waveforms_per_cluster=1E4,controller=controller):
                #make max_waveforms_per_cluster a really big number if you want to get all the waveforms (slow)
                print('Exporting cluster waveforms, max {0} per cluster'.format(max_waveforms_per_cluster))
                if isinstance(cluster_ids,int):
                    cluster_ids=[cluster_ids]
                elif cluster_ids == 'all':
                    cluster_ids=controller.cluster_ids

                for i in range(len(cluster_ids)):
                    all_waveforms = controller._select_data(int(cluster_ids[i]),
                                            controller.all_waveforms,
                                            max_waveforms_per_cluster,
                                            ).data
                    all_waveforms =np.swapaxes(all_waveforms,0,2)
                    print('Exporting {0} waveforms from cluster {1}'.format(all_waveforms.shape[2],cluster_ids[i]))
                    np.save('cluster_waveforms_{0}.npy'.format(cluster_ids[i]),all_waveforms)
                    