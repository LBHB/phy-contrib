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

def find_nearest(array, value):
                        n = [abs(i-value) for i in array]
                        idx = n.index(min(n))
                        return array[idx]


class ExportCelltypes(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_gui_ready(gui):
           
            
            actions = Actions(gui)
            @actions.add(alias='celltypes')            
            def ExportMeanWaveforms(max_waveforms_per_cluster=1E4,controller=controller):
                fs = 30000
                #make max_waveforms_per_cluster a really big number if you want to get all the waveforms (slow)
                cluster_ids=controller.supervisor.clustering.cluster_ids
                mwf=np.zeros((controller.model.n_samples_templates,len(cluster_ids)))
                sp_width = -1*np.ones(len(cluster_ids))  ## Neill and Stryker
                pt_ratio = -1*np.ones(len(cluster_ids))  ## Neill and Stryker
                endslope = -1*np.ones(len(cluster_ids))  ## Neill and Stryker
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
                   
                np.save(op.join(controller.model.dir_path,'endslope.npy'),endslope)
                np.save(op.join(controller.model.dir_path,'peak_trough_ratio.npy'),pt_ratio)    
                np.save(op.join(controller.model.dir_path,'spike_width.npy'),sp_width)        
                np.save(op.join(controller.model.dir_path,'mwf.npy'),mwf)
                print('Done exporting celltype specifiers')
                
                
                
                
                
                
                