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
from phy.gui import Actions
import numpy as np
from phy import IPlugin

#from vispy.app import Canvas
#from vispy import gloo
#from phy.plot import View
import pylab as py

class PlotClusterLocations(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_create_gui(gui):
            
            self.text_handles=[None] * len(controller.cluster_ids)
            self.color=[None] * len(controller.cluster_ids)
            self.text_color=[None] * len(controller.cluster_ids)
            self.fig=[None]
            self.drawn=False
            @gui.connect_
            def on_select(clusters,controller=controller):
                if self.drawn:
                    for i in range(len(controller.cluster_ids)):
                        if any(controller.cluster_ids[i] == clusters):
                            self.text_handles[i].set_color('r')
                        else:
                            self.text_handles[i].set_color(self.text_color[i])
                        
                    self.fig.canvas.draw()
                    self.fig.show()
            
            actions = Actions(gui)
            @actions.add(alias='pcl') #shortcut='ctrl+p',
            def acp(controller=controller):
                print('All Cluster Plot')
                self.drawn=True
                self.text_handles=[None] * len(controller.cluster_ids)
                self.color=[None] * len(controller.cluster_ids)
                self.text_color=[None] * len(controller.cluster_ids)
                cluster_ids=controller.cluster_ids
                height=np.zeros(len(cluster_ids))
                center_of_mass=np.zeros((len(cluster_ids),2))
                use=np.zeros(len(cluster_ids), dtype=bool)
                type=np.zeros(len(cluster_ids), dtype=int)
                for i in range(len(cluster_ids)):
                    data = controller.get_waveforms(int(cluster_ids[i]))[0]
                    height[i]=abs(data.data.mean(0).min())
                    mv=-data.data.mean(0).min(0)
                    mv[mv<0]=0
                    if (any(mv) == False) or (any(-data.data.mean(0).min(0) > data.data.mean(0)[:2].mean(0)) ==  False):
                        #Quick fix for small-amplitude (usually noise) clusters
                        #sets clusters with all mean amplitudes less than zero to have a location defined by get_best_channel instead of a weighted average
                        mv[controller.get_best_channel(cluster_ids[i])]=1
                        
                    mv=mv/mv.sum()
                    center_of_mass[i,:]=(mv*controller.channel_positions.T).sum(1)
                    use[i]=True

                    if controller.cluster_groups[cluster_ids[i]] == 'good':
                        type[i]=3
                        self.color[i]=(0.5255,0.8196,0.4275)
                        self.text_color[i]=(1,1,1)
                    elif controller.cluster_groups[cluster_ids[i]] == 'mua':
                        type[i]=2
                        self.color[i]=(0,.7333,1)
                        self.text_color[i]=(1,1,1)
                    elif controller.cluster_groups[cluster_ids[i]] == 'noise':
                        type[i]=1
                        self.color[i]=(.5,.5,.5)
                        self.text_color[i]=(.5,.5,.5)
                    else:
                        type[i]=0
                        self.color[i]=(1,1,1)
                        self.text_color[i]=(1,1,1)
                
                py.rc('xtick', color='w')        
                py.rc('ytick', color='w')
                py.rc('axes', edgecolor='w')
                self.fig = py.figure()
                ax = self.fig.add_axes([0.15, 0.02, 0.83, 0.975])
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                mngr = py.get_current_fig_manager()
                mngr.window.setGeometry(1700,20,220, 1180)
                rect = self.fig.patch
                rect.set_facecolor('k')
                

                ax.scatter(center_of_mass[:,0], center_of_mass[:,1],height/height.max()*200,facecolors='none', edgecolors=self.color)
                   # inds = np.where(use1)[0]
                   # for j in range(len(inds)):
                   #     self.text_handles[i]=ax.annotate(cluster_ids[inds[j]], (center_of_mass[inds[j],0],center_of_mass[inds[j],1]),color=textcolors[i],fontsize=10)
                for i in range(len(cluster_ids)):
                    self.text_handles[i]=ax.annotate(cluster_ids[i], (center_of_mass[i,0],center_of_mass[i,1]),color=self.text_color[i],fontsize=10)
                
                ax.set_axis_bgcolor('k')
                mins=center_of_mass.min(0)-abs(center_of_mass.min(0)*.1)                
                maxs=center_of_mass.max(0)+abs(center_of_mass.max(0)*.1)
                ax.axis((mins[0],maxs[0],mins[1],maxs[1]))
                self.fig.show()

                #print(center_of_mass)
                #print(height) 
          
          #vispy version, abandoned because I couldn't get view.text to work right
#                view = View()
#                with view.building():
#                    view.scatter(center_of_mass[use,0], center_of_mass[use,1], size=height[use]/height.max()*20, marker='disc')
#                    inds = np.where(use)[0]
#                    for i in range(len(inds)):
#                        print(i)
#                        #view.text(pos=(center_of_mass[inds[i],0],center_of_mass[inds[i],1]), text='hi',anchor=(center_of_mass[inds[i],0],center_of_mass[inds[i],1]))                    
#                    #view.scatter(center_of_mass[:,0], center_of_mass[:,1], color=c, size=s, marker='disc')
#                    #view.scatter(x, y, color=c, size=s, marker='disc')
#                    view.text(pos=(center_of_mass[inds[i],0],center_of_mass[inds[i],1]), text='hi',anchor=(center_of_mass[inds[i],0],center_of_mass[inds[i],1]),data_bounds=None)
#                    view.text(pos=(center_of_mass[inds[i],0],center_of_mass[inds[0],1]), text='hi',anchor=(center_of_mass[inds[0],0],center_of_mass[inds[0],1]),data_bounds=None)
#                view.show()    
                
                
                
                
#                from PyQt4.QtCore import pyqtRemoveInputHook
#                from pdb import set_trace
#                pyqtRemoveInputHook()
#                set_trace()  
                
                                