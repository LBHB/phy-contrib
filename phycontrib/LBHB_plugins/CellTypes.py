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
import matplotlib.pyplot as plt

def find_nearest(array, value):
                        n = [abs(i-value) for i in array]
                        idx = n.index(min(n))
                        return array[idx]


def export_cell_types(controller, groups, max_waveforms_per_cluster=1E3):
        fs = 30000

        original_template_ids = np.load(op.join(controller.model.dir_path,'spike_templates.npy'))

        #make max_waveforms_per_cluster a really big number if you want to get all the waveforms (slow)
        cluster_ids=controller.supervisor.clustering.cluster_ids
        cluster_groups = groups
        mwf=np.zeros((controller.model.n_samples_templates,len(cluster_ids)))
        sp_width = -1*np.ones(len(cluster_ids))
        pt_ratio = -1*np.ones(len(cluster_ids))
        endslope = -1*np.ones(len(cluster_ids))
        c_group_keys = np.sort(np.array([int(x) for x in cluster_groups.keys()]))

        sorted_units_mask = []
        for i in range(0, len(cluster_groups)):
            if cluster_groups[c_group_keys[i]]=='good' or cluster_groups[c_group_keys[i]]=='mua':
                sorted_units_mask.append(1)
            else:
                sorted_units_mask.append(0)
        sorted_units_mask = np.array(sorted_units_mask,dtype=np.bool)

        for i in range(len(cluster_ids)):
            if sorted_units_mask[i]==1:
                print('i={0}, cluster={1}, group={2}'.format(i, cluster_ids[i], cluster_groups[c_group_keys[i]]))

                if len(np.argwhere(controller.get_template_counts(cluster_ids[i])!=0))>1:
                    # this cluster is the result of a merge, figure out which spikes to use for
                    # average
                    templates = np.argwhere(controller.get_template_counts(cluster_ids[i])!=0)
                    counts = controller.get_template_counts(cluster_ids[i])
                    cluster = np.argwhere(counts==np.max(counts[templates]))[0][0]
                    ids_squeezed = original_template_ids.copy().squeeze()
                    valid_spike_ids = np.argwhere(ids_squeezed==cluster)
                    spike_ids = np.random.choice(valid_spike_ids[:,0], int(max_waveforms_per_cluster))

                else:
                    spike_ids = controller.selector.select_spikes([cluster_ids[i]],
                                            max_waveforms_per_cluster,
                                            controller.batch_size_waveforms)

                channel_ids = np.arange(controller.model.n_channels) #gets all chnnels
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

        X = np.vstack((pt_ratio, sw, endslope)).T
        X = X[sorted_units_mask]
        kmeans = KMeans(n_clusters=2, random_state=0).fit(X)

        # create an array of labels (default it is -1) for ALL clusters
        labels_ = -1*np.ones(len(cluster_ids))

        j = 0
        # only save the labels from the clustered (sorted) units. The rest stay
        # as -1
        for i in range(0, len(cluster_ids)):
            if sorted_units_mask[i] == True:
                labels_[i] = kmeans.labels_[j]
                j+=1

        # make sure lableing of fs and rs is consitent. (by default, 0 means regular spiking)
        labels_return = -1*np.ones(len(labels_))
        if np.mean(sw[labels_==1]) > np.mean(sw[labels_==0]):
            labels_return[labels_==1]=0
            labels_return[labels_==0]=1
        else:
            labels_return = labels_

        # plot the clustered waveforms
        f, ax = plt.subplots(1,2)
        ax[0].set_ylabel('endslope')
        ax[0].set_xlabel('spike width')
        ax[0].plot(sp_width[labels_return==1], endslope[labels_return==1], 'r.')
        ax[0].plot(sp_width[labels_return==0], endslope[labels_return==0], 'b.')
        asp = np.diff(ax[0].get_xlim())[0] / np.diff(ax[0].get_ylim())[0]
        ax[0].set_aspect(asp)

        ax[1].set_ylabel('peak trough ratio')
        ax[1].set_xlabel('spike width')
        ax[1].plot(sp_width[labels_return==1], pt_ratio[labels_return==1], 'r.')
        ax[1].plot(sp_width[labels_return==0], pt_ratio[labels_return==0], 'b.')
        ax[1].legend(['FS', 'RS'])
        asp = np.diff(ax[1].get_xlim())[0] / np.diff(ax[1].get_ylim())[0]
        ax[1].set_aspect(asp)


        f.tight_layout()

        plt.savefig(op.join(controller.model.dir_path,'waveform clustering.png'))


        np.save(op.join(controller.model.dir_path, 'wft_celltype.npy'), labels_return)
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
            def on_request_save(*args, controller=controller):
                if len(args) == 6:
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
                export_cell_types(controller=controller, groups=groups)
