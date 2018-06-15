    #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 14:37:48 2017

@author: hellerc
"""

'''
Built off Luke's function to export mean waveforms

Snippet used to export relevant information for clustering cell types.
-mean waveforms
-spike width
-full width half max
-peak to trough ratio
-endslope

(see below for instructions on how to call this snippet)
       
       *** replace 'emw' with 'celltypes' ***

====== Luke's docstring ======

ExportMeanWaveforms output plugin.
This plugin creates a npy file containing an array of the mean waveform for 
each cluster (N_channels,N_samples,N_clusters)
This plugin is called a snippet. To use it type ':' to get into snippet mode,
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
Luke Shaheen - Laboratory of Brain, Hearing and Behavior Nov 2016

==============================
'''

from phy.gui import Actions
import numpy as np
from phy import IPlugin
import os.path as op
from scipy import interpolate
from sklearn.cluster import KMeans

def find_nearest(array, value):
                        n = [abs(i-value) for i in array]
                        idx = n.index(min(n))
                        return array[idx]
def export_cell_types(controller, max_waveforms_per_cluster=1E3):
        fs = 30000
        #make max_waveforms_per_cluster a really big number if you want to get all the waveforms (slow)
        cluster_ids=controller.supervisor.clustering.cluster_ids
        cluster_groups = controller.model.get_metadata('group')
        mwf=np.zeros((controller.model.n_samples_templates,len(cluster_ids)))
        sp_width = -1*np.ones(len(cluster_ids))  ## Neill and Stryker
        pt_ratio = -1*np.ones(len(cluster_ids))  ## Neill and Stryker
        endslope = -1*np.ones(len(cluster_ids))  ## Neill and Stryker
        
        cluster_groups = np.array([[k, v] for k, v in cluster_groups.items()])    
        single_units = np.array([0 if cluster_groups[i,1]!='good' else cluster_ids[i] for i in range(0,len(cluster_ids))])
        single_unit_indices = np.argwhere(np.array(cluster_ids)==single_units)
        single_unit_indices = [x[0] for x in single_unit_indices]
    
        for i in range(len(cluster_ids)):
            print('i={0},cluster={1}'.format(i,cluster_ids[i]))
            spike_ids = controller.selector.select_spikes([cluster_ids[i]],
                                        max_waveforms_per_cluster,
                                        controller.batch_size_waveforms)
            #channel_ids = controller.get_best_channels(cluster_ids[i])
            channel_ids=np.arange(controller.model.n_channels_dat) #gets all chnnels
            data = controller.model.get_waveforms(spike_ids, channel_ids)
            datam = np.rollaxis(data.mean(0),1)
            best_channel = np.argwhere(np.max(abs(datam),1) == np.max(np.max(abs(datam),1)))
            spike = np.squeeze(datam[best_channel, :])
            
            if abs(np.min(spike)) < np.max(spike):
                spike = -spike  # flip spike if it had positive depolarization
            
            peak = np.max(abs(spike[20:60]))
            fit2 = interpolate.UnivariateSpline(np.arange(len(spike)), spike)
            pts = 10000
            fs_spl = fs*(pts/len(spike))
            mwf[:,i] = spike
        
           
            spl = -fit2(np.linspace(0,len(spike),pts))
            ind=(np.argwhere(spl == max(spl)))[0][0]
            peak = np.argwhere(spl[:ind]==
                               find_nearest(spl[:ind], max(spl)))
            trough = np.argwhere(spl[ind:]==
                               find_nearest(spl[ind:], min(spl)))+ind
            sp_width[i] = ((abs(peak[0][0]-trough[0][0])/(pts))*len(spike))/fs*1000  ## convert width to ms
            pt_ratio[i] = abs(spl[trough])/abs(spl[peak])
            
            ## Where to calculate endslope(0.5ms post spike peak)
            inds_from_peak = round((0.5/1000)*fs_spl)   #Niell and Stryker
            ind_slope = peak + inds_from_peak
            step = round((0.025/1000)*fs_spl)  # 0.025 ms surrounding the location
            if ind_slope+step < pts:
                endslope[i] = (spl[ind_slope+step] - spl[ind_slope-step])/(step*2)
           
        np.save(op.join(controller.model.dir_path,'wft_endslope.npy'),endslope)
        np.save(op.join(controller.model.dir_path,'wft_peak_trough_ratio.npy'),pt_ratio)    
        np.save(op.join(controller.model.dir_path,'wft_spike_width.npy'),sp_width)        
        np.save(op.join(controller.model.dir_path,'wft_mwf.npy'),mwf)
        print('Done exporting celltype specifiers')
        
        path = controller.model.dir_path
        pt_ratio = np.load(path+'/wft_peak_trough_ratio.npy')
        sw = np.load(path+'/wft_spike_width.npy')
        
        X = np.vstack((pt_ratio, sw)).T
        kmeans = KMeans(n_clusters=2, random_state=0).fit(X)
        labels_ = kmeans.labels_
        # deprecated code if you only want to label single units
        '''
        labels_ = -1*np.ones(len(cluster_ids))
        
        for i in range(0, len(cluster_ids)):
            if i in single_unit_indices:
                labels_[i] = kmeans.labels_[i]
        '''       
                    
        np.save(op.join(controller.model.dir_path, 'wft_celltype.npy'), labels_)
        print('Done exporting classified waveform types')
        
            
class ExportCellTypes(IPlugin):

    def attach_to_controller(self, controller):
        @controller.connect
        def on_gui_ready(gui, **kwargs):           
            
            actions = Actions(gui)
            @actions.add(alias='celltypes')            
            def ExportCellTypes(max_waveforms_per_cluster=1E3,controller=controller):
                export_cell_types(controller, max_waveforms_per_cluster)
                
            @controller.supervisor.connect
            def on_request_save(spike_clusters, groups, labels, controller=controller): 
                export_cell_types(controller=controller)
                
                
                
                
                