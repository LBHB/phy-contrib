"""PlotClusterLocations view plugin.

This plugin pops up a matplotlib figure showing the location of each cluster by 
a weighted mean of its mean spike height for each channel.
Size of circle indicates mean spike height for the biggest channel.

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['PlotClusterLocations']
```
Luke Shaheen - Laboratory of Brain, Hearing and Behavior Nov 2015
"""

from phy.gui import Actions
import numpy as np
from phy import IPlugin
import os.path as op

#from vispy.app import Canvas
#from vispy import gloo
#from phy.plot import View
import pylab as py

class PlotClusterLocations(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_gui_ready(gui):

            cluster_ids=controller.supervisor.clustering.cluster_ids
            self.text_handles=[None] * len(cluster_ids)
            self.color=[None] * len(cluster_ids)
            self.text_color=[None] * len(cluster_ids)
            self.fig=[None]
            self.drawn=False
            @gui.connect_
            def on_select(clusters,controller=controller,**kwargs):
                if self.drawn:
                    for i in range(len(cluster_ids)):
                        if any(cluster_ids[i] == clusters):
                            self.text_handles[i].set_color('r')
                        else:
                            self.text_handles[i].set_color(self.text_color[i])
                        
                    self.fig.canvas.draw()
                    self.fig.show()
            
            actions = Actions(gui)
            @actions.add(alias='pcl') #shortcut='ctrl+p',
            def PlotClusterLocations(controller=controller):
                cluster_ids=controller.supervisor.clustering.cluster_ids
                print('Plotting Cluster Locations')
                self.drawn=True
                self.text_handles=[None] * len(cluster_ids)
                self.color=[None] * len(cluster_ids)
                self.text_color=[None] * len(cluster_ids)
                height=np.zeros(len(cluster_ids))
                center_of_mass=np.zeros((len(cluster_ids),2))
                type=np.zeros(len(cluster_ids), dtype=int) 
                for i in range(len(cluster_ids)):
                    mv=np.zeros(controller.model.n_channels_dat)
                    data = controller._get_waveforms(int(cluster_ids[i]))
                    height[i]=abs(data.data.mean(0).min())
                    mv[data.channel_ids]=-data.data.mean(0).min(0)
                    mv[mv<0]=0
                    if (any(mv) == False) or (any(-data.data.mean(0).min(0) > data.data.mean(0)[:2].mean(0)) ==  False):
                        #Quick fix for small-amplitude (usually noise) clusters
                        #sets clusters with all mean amplitudes less than zero to have a location defined by get_best_channel instead of a weighted average
                        mv[controller.get_best_channel(cluster_ids[i])]=1
                        
                    mv=mv/mv.sum()
                    center_of_mass[i,:]=(mv*controller.model.channel_positions.T).sum(1)

                    if controller.model.n_channels == 128:
                        # LAS hack to make 128D cluster locations look better
                        if center_of_mass[i,0] > 200 and center_of_mass[i,0] < 500 :
                            center_of_mass[i,0] = center_of_mass[i,0]- 200
                            center_of_mass[i,1] = center_of_mass[i,1]- 1000
                        if center_of_mass[i,0] > 600 and center_of_mass[i,0] < 800 :
                            center_of_mass[i,0] = center_of_mass[i,0]- 400
                            center_of_mass[i,1] = center_of_mass[i,1]- 2000
                        if center_of_mass[i,0] > 800 :
                            center_of_mass[i,0] = center_of_mass[i,0]- 600
                            center_of_mass[i,1] = center_of_mass[i,1]- 3000
                    if cluster_ids[i] not in controller.supervisor.cluster_groups.keys() or controller.supervisor.cluster_groups[cluster_ids[i]] == '':
                        type[i]=0
                        self.color[i]=(1,1,1)
                        self.text_color[i]=(1,1,1)
                    elif controller.supervisor.cluster_groups[cluster_ids[i]] == 'good':
                        type[i]=3
                        self.color[i]=(0.5255,0.8196,0.4275)
                        self.text_color[i]=(1,1,1)
                    elif controller.supervisor.cluster_groups[cluster_ids[i]] == 'mua':
                        type[i]=2
                        self.color[i]=(0,.7333,1)
                        self.text_color[i]=(1,1,1)
                    elif controller.supervisor.cluster_groups[cluster_ids[i]] == 'noise':
                        type[i]=1
                        self.color[i]=(.5,.5,.5)
                        self.text_color[i]=(.5,.5,.5)
                    else:
                        from PyQt4.QtCore import pyqtRemoveInputHook
                        from pdb import set_trace
                        pyqtRemoveInputHook()
                        set_trace() 
                        raise RuntimeError('Cluster group ({}) of cluster {} is unknown.'
                            .format(controller.supervisor.cluster_groups[cluster_ids[i]],cluster_ids[i]))                    
                
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
                save_path = op.join(controller.model.dir_path,'cluster_centers_of_mass.npy')
                np.save(save_path,center_of_mass)
                print('Cluster centers of mass exported to {}'.format(save_path))
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

                
                                