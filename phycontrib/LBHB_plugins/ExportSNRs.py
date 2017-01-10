"""ExportSNRs output plugin.

This plugin creates a npy file containing an array of the snrs for 
each cluster (N_channels,N_clusters)

This plugin is called a s ansippet. To use it type ':' to get into snippet mode,
then type:
esnr
or 
emw N
where N is the max number of waveforms per cluster to use to measure snr (default 1000)
use a really high number to use all waveforms.


To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['ExportSNRs']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Dec 2016
"""

from phy.gui import Actions
import numpy as np
from phy import IPlugin
import os.path as op

class ExportSNRs(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_gui_ready(gui):
           
            
            actions = Actions(gui)
            @actions.add(alias='esnr',menu='Export',name='Export SNRs')            
            def ExportSNRs(max_waveforms_per_cluster=1E3,controller=controller):
                #make max_waveforms_per_cluster a really big number if you want to get all the waveforms (slow)
                print('Exporting SNRs')
                cluster_ids=controller.supervisor.clustering.cluster_ids
                snr=np.zeros((controller.model.n_channels_dat,len(cluster_ids)))
                snr[:] = np.NAN
                for i in range(len(cluster_ids)):
                    print('i={0},cluster={1}'.format(i,cluster_ids[i]))                    
                    if max_waveforms_per_cluster == 100 :
                        all_data = controller._get_waveforms(int(cluster_ids[i]))
                        data=all_data.data
                        channel_ids=all_data.channel_ids
                    else:
                        spike_ids = controller.selector.select_spikes([cluster_ids[i]],
                                                max_waveforms_per_cluster,
                                                controller.batch_size_waveforms,
                                                #subset='random', to get a random subset
                                                )
                        #channel_ids = controller.get_best_channels(cluster_ids[i])
                        channel_ids=np.arange(controller.model.n_channels_dat) #gets all chnnels
                        data = controller.model.get_waveforms(spike_ids, channel_ids)              
                    noise_std=np.concatenate((data[:,:10,:],data[:,:10,:]),axis=1).std(axis=(0,1))
                    sig_std=data.mean(0).std(0)
                    snr[channel_ids,i]=sig_std/noise_std
                        
                np.save(op.join(controller.model.dir_path,'snrs.npy'),snr)
                print('Done exporting snrs')