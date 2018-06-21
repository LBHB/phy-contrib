"""Feature template projection vs time view plugin.

This plugin adds an interactive vispy figure showing the projection of selected 
spikes onto the templatre of the first cluster vs time

To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['FeatureTemplateTimeView']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Jan 2017
"""

from phy import IPlugin
from phy.utils import Bunch
import numpy as np
from phy.plot.transform import Range
from phy.cluster.views.scatter import ScatterView
import os.path as op
import phy.gui.qt as QtGui

class FeatureTemplateTime(ScatterView):
    _callback_delay = 100
    def __init__(self,
                 coords=None,  # function clusters: Bunch(x, y)
                 sample_rate=None,
                 path=None,
                 cont=None,
                 gui=None,
                 **kwargs):

        if coords is None:
            coords=self.get_template_projections
        assert coords
        self.coords = coords
        self.controller=cont
        self.gui=gui
        blocksizes_path=op.join(path,'blocksizes.npy')
        if op.exists(blocksizes_path):
            self.blocksizes=np.load(blocksizes_path)[0]
            self.blockstarts=np.load(op.join(path,'blockstarts.npy'))[0]
            self.blocksizes_time=self.blocksizes/sample_rate
            self.blockstarts_time=self.blockstarts/sample_rate
            self.gap=np.diff(self.blockstarts)-self.blocksizes[:-1]
            self.gap_time=np.diff(self.blockstarts_time)-self.blocksizes_time[:-1]
            self.show_block_gap=False
            self.show_block_lines=True 
        else:
            self.show_block_gap=False
            self.show_block_lines=False
        # Initialize the view.
        super(ScatterView, self).__init__(enable_lasso=True,
                                          **kwargs)
        #self.canvas.events.mouse_press.connect(self.on_mouse_press)
        if self.show_block_lines:
            @self.controller.supervisor.actions.add(menu='FeatureTemplateTimeView',name='Toggle show block gaps')   
            def toggle_show_block_gap(self=self,sup=self.controller.supervisor):
                self.show_block_gap = not self.show_block_gap             
                self.on_select()
        self.currentline=[None] * 3
        self.data_bounds=None
        
        gui.connect_(self.on_request_split_FTT)
        
        @gui.connect_
        def on_time_change(self=self, time=None, **kwargs):
            print('Time Change to {0}'.format(time.time))
# takes too long,             
#            line2=self.lines(pos=[time.time, self.data_bounds[1],time.time,self.data_bounds[3]],color=(0, 0, 1, 1),data_bounds=self.data_bounds)
#            self.currentline.pos[0][0]=time.time
#            self.currentline.pos[0][2]=time.time
#            self.currentline.update()
#            #self.view.update()
#            self.update()
#	     self.show()





            
    def on_select(self, cluster_ids=None, **kwargs):
        super(ScatterView, self).on_select(cluster_ids, **kwargs)
        cluster_ids = self.cluster_ids
        n_clusters = len(cluster_ids)
        if n_clusters == 0:
            return

        # Retrieve the data.
        bunchs = self._get_data(cluster_ids)

        # Compute the data bounds.
        data_bounds = self._get_data_bounds(bunchs)
        if self.show_block_gap:                    
            line_times=self.blockstarts_time
            grey_line_times = self.blockstarts_time[1:]-self.gap_time
            data_bounds = (0, data_bounds[1],self.controller.model.duration+self.gap_time.sum(), data_bounds[3])
        else:
            data_bounds = (0,data_bounds[1], self.controller.model.duration, data_bounds[3])
            if self.show_block_lines:                    
                line_times = self.blocksizes_time[:-1].cumsum()
        self.data_bounds=data_bounds
        if len(bunchs) > 1:
            pass
           # data_bounds = (data_bounds[0], 0, data_bounds[2], data_bounds[3])
        # Plot the points.
        with self.building():
            self._plot_points(bunchs, data_bounds)  
            if self.show_block_lines:
                for time in line_times:
                    self.lines(pos=[time, data_bounds[1], time, data_bounds[3]],color=(1, 1, 1, 1),data_bounds=data_bounds)
            if self.show_block_gap:
               for time in grey_line_times:
                    self.lines(pos=[time, data_bounds[1], time, data_bounds[3]],color=(.4, .4, .4, 1),data_bounds=data_bounds)
            liney = 0.
            self.lines(pos=[[data_bounds[0], liney, data_bounds[2], liney]],
                   data_bounds=data_bounds,
                   color=(1., 1., 1., .5),
                   )
            self.lines(pos=[0, data_bounds[1], 0, data_bounds[3]],color=(.4, .4, .4, 1),data_bounds=data_bounds)
            self.lines(pos=[data_bounds[2], data_bounds[1],data_bounds[2], data_bounds[3]],color=(.4, .4, .4, 1),data_bounds=data_bounds)
            time=self.gui.get_view('TraceView').time
            half_duration=self.gui.get_view('TraceView').half_duration
            self.currentline[0]=self.lines(pos=[time, data_bounds[1],time, data_bounds[3]],color=(1, 0, 0, 1),data_bounds=data_bounds)
            self.currentline[1]=self.lines(pos=[time-half_duration, data_bounds[1],time-half_duration, data_bounds[3]],color=(.4, 0, 0, 1),data_bounds=data_bounds)
            self.currentline[2]=self.lines(pos=[time+half_duration, data_bounds[1],time+half_duration, data_bounds[3]],color=(.4, 0, 0, 1),data_bounds=data_bounds)
    def _get_data(self, cluster_ids):
        b = self.coords(cluster_ids)
        return b
    def get_template_projections(self,cluster_ids):
        if len(cluster_ids) < 1 :
            return None

        ni = self.controller.get_template_counts(cluster_ids[0])
        x_min=np.inf
        x_max=-np.inf
        y_min=np.inf
        y_max=-np.inf
        out=list()
        for cid in cluster_ids:
            si = self.controller._get_spike_ids(cid, self.controller.n_spikes_features)
            ti = self.controller.model.get_template_features(si)
            x  = np.copy(self.controller.model.spike_times[si])
            y  = np.average(ti, weights=ni, axis=1)
            if self.show_block_gap:
                for j in range(len(self.gap_time)):                     
                    x[np.logical_and(self.controller.model.spike_times[si]>self.blocksizes_time[:j+1].sum(),self.controller.model.spike_times[si]<self.blocksizes_time[:j+2].sum())]+=self.gap_time[:j+1].sum()

            # Compute the data bounds.
            x_min = min(x.min(), x_min)
            y_min = min(y.min(), y_min)
            x_max = max(x.max(), x_max)
            y_max = max(y.max(), y_max)
            out.append(Bunch(x=x, y=y, spike_ids=si))
        data_bounds = (x_min, y_min, x_max, y_max)
        for i in range(len(out)):
            out[i].data_bounds=data_bounds

        return out
    
    def on_mouse_press(self, e):
        # Get mouse position in NDC.
        mouse_pos = self.panzoom.get_mouse_pos(e.pos)
        if self.show_block_gap:
            total_time=(mouse_pos[0]+1)/2*(self.controller.model.duration+self.gap_time.sum())
            msg='Total time = {:0.0f} ms re start'.format(total_time)
        else:
            clicked_time=(mouse_pos[0]+1)/2*self.controller.model.duration
        msg='Clicked time = {:0.0f} ms re start'.format(clicked_time)
        self.controller.status_message=msg
        print(msg)
        if 'Control' in e.modifiers and e.button == 2:
            tv = self.gui.get_view('TraceView')
            tv.go_to(clicked_time)
            self.on_select()
        elif 'Shift' in e.modifiers:
            self.panzoom.set_pan_zoom(zoom=[.99, .97],pan=[0, 0])

    def on_request_split_FTT(self):
        """Return the spikes enclosed by the lasso."""


        if (self.lasso.count < 3 or
                not len(self.cluster_ids)):  # pragma: no cover
            return np.array([], dtype=np.int64)
        #assert len(self.channel_ids)
        
        id_str = [str(id) for id in self.cluster_ids]
        
        dlg = QtGui.QInputDialog(None)
        [cl,ok] = QtGui.QInputDialog.getItem(dlg,"Which cluster id should be split:", 
           "Which cluster id should be split:", id_str, 0, False)
        if not  ok:
             return np.array([], dtype=np.int64)
        cluster_index=id_str.index(cl)
                        
        bunchs = self._get_data(self.cluster_ids)
        pos=np.vstack((bunchs[cluster_index]['x'],bunchs[cluster_index]['y'])).transpose()
        # Normalize the points.
        ra = Range(self.data_bounds)
        pos = ra.apply(pos)
        # Find lassoed spikes.
        ind = self.lasso.in_polygon(pos)
        ids=bunchs[cluster_index]['spike_ids'][ind]
        self.lasso.clear()
        return np.unique(ids)
        
class FeatureTemplateTimeView(IPlugin):

                
    def attach_to_controller(self, controller):
        self.controller=controller
        # Create the figure when initializing the GUI.
        @controller.connect
        def on_gui_ready(gui):
            # Called when the GUI is created.
            view = FeatureTemplateTime(sample_rate=controller.model.sample_rate,path=controller.model.dir_path,cont=controller,gui=gui)
#            @gui.connect_
#            def on_select(clusters):
#                
#                with view.building():
#                    #view.scatter(x, y, color=c, size=s, marker='square')
#                    colors = _spike_colors(np.arange(len(clusters)))      
#                    
#                    for i in range(len(clusters)):
#                        coords=controller.get_amplitudes(clusters[i])                   
#                        view[0].scatter(x=coords.x,y=coords.y, 
#                                    color=colors[i], 
#                                    size=3, 
#                                    marker='disc',
#                                    )
#                        #sp=view[1].hist(coords.y,color=(1,0,0,1),100)
#                        ah=vis.HistogramVisual(coords.y,bins=100,color=(1,0,0,1),orientation='v') #how to add this to view[1] ??
#                view.show()
            controller._add_view(gui,view)
            #gui.add_view(view, name='AmplitudeViewWithHistogram')

