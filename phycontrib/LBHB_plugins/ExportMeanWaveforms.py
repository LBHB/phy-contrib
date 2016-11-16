"""ExportMeanWaveforms output plugin.

This plugin creates a npy file containing an array of the mean waveform for 
each cluster (N_channels,N_samples,N_clusters)

This plugin is called a s ansippet. To use it type ':' to get into snippet mode,
then type:
emw
or 
emw N
where N is the max number of waveforms per cluster to use to create the mean waveform (default 1000)
use a really high number to use all waveforms.


To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['ExportMeanWaveforms']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Nov 2015
"""

from phy.gui import Actions
import numpy as np
from phy import IPlugin

class ExportMeanWaveforms(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_create_gui(gui):
           
            
            actions = Actions(gui)
            @actions.add(alias='emw')            
            def ExportMeanWaveforms(max_waveforms_per_cluster=1E4,controller=controller):
                #make max_waveforms_per_cluster a really big number if you want to get all the waveforms (slow)
                print('Exporting mean waveforms')
                cluster_ids=controller.cluster_ids
                mean_waveforms=np.zeros((controller.n_channels,controller.n_samples_templates,len(cluster_ids)))
                for i in range(len(cluster_ids)):
                    print('i={0},cluster={1}'.format(i,cluster_ids[i]))
                    all_waveforms = controller._select_data(int(cluster_ids[i]),
                                            controller.all_waveforms,
                                            max_waveforms_per_cluster,
                                            )
                    mean_waveforms[:,:,i]=np.rollaxis(all_waveforms.data.mean(0),1)
                np.save('mean_waveforms.npy',mean_waveforms)
                print('Done exporting mean waveforms')