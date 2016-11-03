# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 13:54:59 2016

@author: luke
"""

#def decorator(function):
#    controller.callbacks.append(function)
#    return function
#        
#
#@decorator
#def foo(*args, **kwargs):
#    pass
#
## equivalent
#def foo(*args, **kwargs):
#    pass
#foo = decorator(foo)

import numpy as np

from phy import IPlugin

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
                np.save('best_channels.npy',best_channels)
                                