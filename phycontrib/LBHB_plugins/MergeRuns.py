"""Merge runs plugin.

This plugin creates a second instance of phy and a gui to label clusters that 
can from the same neuron

This plugin is called as a snippet. To use it type ':' to get into snippet mode,
then type:
mr


To activate the plugin, copy this file to `~/.phy/plugins/` and add this line
to your `~/.phy/phy_config.py`:

```python
c.TemplateGUI.plugins = ['MergeRuns']
```

Luke Shaheen - Laboratory of Brain, Hearing and Behavior Dec 2016
"""

from phy.gui import Actions, GUI
import numpy as np
import matplotlib.pyplot as plt
from phy import IPlugin
from phycontrib import TemplateController
from phy.utils._misc import _read_python
from PyQt4 import QtGui
from PyQt4.QtCore import * 
import sys
import csv
import os.path as op
import time
#from .QtCore import QObject, QTimer, QEvent, QThread
#from .QtGui import QApplication


def create_mean_waveforms(controller,max_waveforms_per_cluster=1E4,cluster_ids=None):
    if cluster_ids is None: 
        cluster_ids=controller.supervisor.clustering.cluster_ids
    else:
        cluster_ids=np.atleast_1d(cluster_ids)
    mean_waveforms=np.zeros((controller.model.n_channels_dat,controller.model.n_samples_templates,len(cluster_ids)))
    print(len(cluster_ids))
    for i in range(len(cluster_ids)):
        #print('i={0},cluster={1}'.format(i,cluster_ids[i]))
        print('{}'.format(i),end=' ')
        sys.stdout.flush()
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
        mean_waveforms[channel_ids,:,i]=np.rollaxis(data.mean(0),1)
    return mean_waveforms

def calc_dists(controller,controller2,m_inds,s_inds=None):
    if s_inds is None:
        s_inds=np.arange(controller2.supervisor.clustering.cluster_ids.shape[0])
    m_inds=np.atleast_1d(m_inds)
    s_inds=np.atleast_1d(s_inds)
    shifts=np.arange(-4,4)
    dists=np.zeros((len(m_inds),len(s_inds)))
    dist=np.zeros(len(shifts))
    for i in range(len(m_inds)):
        for j in range(len(s_inds)):
            if m_inds[i] < 0:
                dists[i,j]=-1
            else:
                for s in range(len(shifts)):
                    diffs = controller.mean_waveforms[:,:,m_inds[i]]-np.roll(controller2.mean_waveforms[:,:,s_inds[j]],shifts[s],axis=1)
                    if shifts[s]<0:
                        dist[s] = np.linalg.norm(diffs[:,:shifts[s]])
                    else:                        
                        dist[s] = np.linalg.norm(diffs[:,shifts[s]:])
                dists[i,j]=dist.min()
    return dists
def load_metadata(filename,cluster_ids):
    from PyQt4.QtCore import pyqtRemoveInputHook
    from pdb import set_trace
    pyqtRemoveInputHook()
    set_trace()  
    unit_types = np.zeros(cluster_ids.shape)
    channels = np.zeros(cluster_ids.shape)
    unit_numbers = np.zeros(cluster_ids.shape)
    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        # Skip the header.
        for row in reader:
            break
        for row in reader:
            cluster, unit_type, channel, unit_number = row
            cluster = int(cluster)
            matchi = cluster == cluster_ids
            if ~np.any(matchi):
                raise RuntimeError('Cluster number {} from {} did not match any'
                'clusters in the current phy. This likely means work was done on '
                'this phy after merging with a previous master. Not sure how to deal'
                'with this!'.format(cluster,filename))
            unit_types[matchi] = unit_type
            channels[matchi] = channel
            unit_numbers[matchi] = unit_number
    return unit_types, channels, unit_numbers
          
class MergeRuns(IPlugin):
        
    def attach_to_controller(self, controller):
        @controller.connect
        def on_gui_ready(gui, plugin=self):

            actions = Actions(gui)
            @actions.add(alias='mr')            
            def MergeRuns(controller=controller, plugin=plugin):
                if False:
                    path2 = QtGui.QFileDialog.getExistingDirectory(
                    None,
                    "Select the results folder for the sort to be merged",
                    op.dirname(op.dirname(controller.model.dir_path)), #two folders up from the current phy's path
                    QtGui.QFileDialog.ShowDirsOnly
                    )
                else:
                    path2='/home/luke/KiloSort_tmp/BOL005c_9_96clusts/results'
                params_path=op.join(path2,'params.py')
                params = _read_python(params_path)
                params['dtype'] = np.dtype(params['dtype'])
                params['path']=path2
                if op.realpath(params['dat_path']) != params['dat_path'] :
                    params['dat_path']=op.join(path2,params['dat_path'])
                print('Loading {}'.format(path2))                
                controller2=TemplateController(**params)
                #controller2.gui_name = 'TemplateGUI2'
                gui2 = controller2.create_gui()
                gui2.show()
                                
#                @gui2.connect_
#                def on_select(clusters,controller2=controller2):  
#                    controller.supervisor.select(clusters)

                    
                #create mean_waveforms for each controller (run)
                print('computing mean waveforms for master run...')
                controller.mean_waveforms=create_mean_waveforms(controller,max_waveforms_per_cluster=100)
                print('computing mean waveforms for slave run...')
                controller2.mean_waveforms=create_mean_waveforms(controller2,max_waveforms_per_cluster=100) 

                groups = {c: controller.supervisor.cluster_meta.get('group', c) or 'unsorted' for c in controller.supervisor.clustering.cluster_ids}
                groups2 = {c: controller2.supervisor.cluster_meta.get('group', c) or 'unsorted' for c in controller2.supervisor.clustering.cluster_ids}
                su_inds=np.nonzero([controller.supervisor.cluster_meta.get('group', c) == 'good' for c in controller.supervisor.clustering.cluster_ids])[0]
                mu_inds=np.nonzero([controller.supervisor.cluster_meta.get('group', c) == 'mua' for c in controller.supervisor.clustering.cluster_ids])[0]
                su_best_channels=np.array([controller.get_best_channel(c) for c in controller.supervisor.clustering.cluster_ids[su_inds]])
                mu_best_channels=np.array([controller.get_best_channel(c) for c in controller.supervisor.clustering.cluster_ids[mu_inds]])
                su_order=np.argsort(su_best_channels)
                mu_order=np.argsort(mu_best_channels)
                m_inds=np.concatenate((su_inds[su_order],mu_inds[mu_order]))

                filename=op.join(controller.model.dir_path,'cluster_names.tsv')
                if not op.exists(filename):                
                    best_channels=np.concatenate((su_best_channels[su_order],mu_best_channels[mu_order]))
                    unit_type=np.concatenate((np.ones(len(su_order)),2*np.ones(len(mu_order))))
                    unit_number=np.zeros(len(best_channels))
                    for chan in np.unique(best_channels):
                        matched_clusts=best_channels==chan
                        unit_number[matched_clusts]=np.arange(sum(matched_clusts))+1
                else: 
                    print('{} exists, loading'.format(filename))
                    unit_types, channels, unit_numbers = load_metadata(filename,controller.supervisor.clustering.cluster_ids)
                    best_channels=channels[m_inds]
                    unit_number=unit_numbers[m_inds]
                    unit_type=unit_types[m_inds]
                    unit_type_current=np.concatenate((np.ones(len(su_order)),2*np.ones(len(mu_order))))
                    if ~np.all(unit_type==unit_type_current):
                        raise RuntimeError('For the master phy, the unit types saved in "cluster_names.tsv"' 
                        'do not match those save in "cluster_groups.tsv" This likely means work was done on '
                        'this phy after merging with a previous master. Not sure how to deal with this!')
                    #re-sort to make unit numbers in order
                    # assuming unit_type is already sorted (which it should be...)                    
                    nsu=np.sum(unit_type==1)
                    su_order=np.lexsort((unit_number[:nsu],best_channels[:nsu]))
                    mu_order=np.lexsort((unit_number[nsu:],best_channels[nsu:]))
                    m_inds[:nsu]=m_inds[su_order]
                    m_inds[nsu:]=m_inds[mu_order+nsu]
                    best_channels=channels[m_inds]
                    unit_number=unit_numbers[m_inds]
                    unit_type=unit_types[m_inds]
                
                dists=calc_dists(controller,controller2,m_inds)
                        
                so=np.argsort(dists,0)
                matchi=so[0,:] #best match index to master for each slave
                sortrows=np.argsort(matchi)#sort index for best match  

                def handle_item_clicked(item,controller=controller,controller2=controller2,plugin=plugin):
                    row = np.array([cell.row() for cell in table.selectedIndexes()])
                    column = np.array([cell.column() for cell in table.selectedIndexes()])
                    print("Row {} and Column {} was clicked".format(row,column))                    
                    print("M {} S {} ".format(controller.supervisor.clustering.cluster_ids[plugin.m_inds[column]], controller2.supervisor.clustering.cluster_ids[plugin.sortrows[row]]))
                    column=column[~np.in1d(plugin.m_inds[column] ,(-1,-2))]
                    if len(column) == 0:
                        pass
                        #controller.supervisor.select(None)  
                        # make a deselect function and call it here if feeling fancy
                    else:
                        controller.supervisor.select(controller.supervisor.clustering.cluster_ids[plugin.m_inds[column]].tolist())                    
                    controller2.supervisor.select(controller2.supervisor.clustering.cluster_ids[plugin.sortrows[row]].tolist())
                    #print("Row %d and Column %d was clicked" % (row, column))                    
    
                def create_table(controller,controller2,plugin): 
                    plugin.table.setRowCount(len(plugin.matchi))
                    plugin.table.setColumnCount(len(plugin.m_inds))
                     
                     # set data
                    dists_txt=np.round(plugin.dists/plugin.dists.max()*100)
                    normal = plt.Normalize(plugin.dists[plugin.dists!=-1].min()-1, plugin.dists.max()+1)
                    colors=plt.cm.viridis_r(normal(plugin.dists))*255                   
                    for col in range(len(plugin.m_inds)):
                        for row in range(len(plugin.matchi)):
                            if plugin.dists[col,plugin.sortrows[row]] < 0:
                                item=QtGui.QTableWidgetItem('N/A')
                                item.setBackground(QtGui.QColor(127,127,127))
                            else:
                                item=QtGui.QTableWidgetItem('{:.0f}'.format(dists_txt[col,plugin.sortrows[row]]))                        
                                item.setBackground(QtGui.QColor(colors[col,plugin.sortrows[row],0],colors[col,plugin.sortrows[row],1],colors[col,plugin.sortrows[row],2]))
                            if plugin.matchi[plugin.sortrows[row]] == col:
                                item.setForeground(QtGui.QColor(255,0,0))
                            #item.setFlags(Qt.ItemIsEditable)
                            plugin.table.setItem(row,col,item)
                            #plugin.table.item(row,col).setForeground(QtGui.QColor(0,255,0)) 
                    for col in range(plugin.dists.shape[0]):
                        if plugin.m_inds[col] == -1:
                            cluster_num='None'
                        elif plugin.m_inds[col] == -2:
                            cluster_num='Noise'
                        else:
                            cluster_num=controller.supervisor.clustering.cluster_ids[plugin.m_inds[col]]
                        plugin.table.setHorizontalHeaderItem(col, QtGui.QTableWidgetItem('{}\n{:.0f}-{:.0f}'.format(cluster_num,plugin.best_channels[col],plugin.unit_number[col])))
                        #plugin.table.setHorizontalHeaderItem(row, QtGui.QTableWidgetItem('{:.0f}'.format(controller.supervisor.clustering.cluster_ids[plugin.m_inds[row]])))
                    for col in range(plugin.dists.shape[1]):
                        c_id=controller2.supervisor.clustering.cluster_ids[plugin.sortrows[col]]
                        #height=controller2.supervisor.cluster_view._columns['height']['func'](c_id)
                        snr=controller2.supervisor.cluster_view._columns['snr']['func'](c_id)
                        plugin.table.setVerticalHeaderItem(col, QtGui.QTableWidgetItem('{:.0f}-{:.1f}'.format(c_id,snr)))
                    plugin.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
                    plugin.table.resizeColumnsToContents()
                    plugin.table.itemClicked.connect(handle_item_clicked)
    

#                self.fig = plt.figure()
#                ax = self.fig.add_axes([0.15, 0.02, 0.83, 0.975])
#                normal = plt.Normalize(dists.min()-1, dists.max()+1)
#                dists_txt=np.round(dists/dists.max()*100)
#                self.table=ax.table(cellText=dists_txt, rowLabels=controller.supervisor.clustering.cluster_ids[m_inds], colLabels=controller2.supervisor.clustering.cluster_ids, 
#                    colWidths = [0.03]*dists.shape[1], loc='center', 
#                    cellColours=plt.cm.hot(normal(dists)))
#                self.fig.show()
                #a = QApplication(sys.argv)

                
                tablegui = GUI(position=(400, 200), size=(400, 300))
                table = QtGui.QTableWidget()
                table.setWindowTitle("Merge Table")
                #table.resize(600, 400)

                plugin.matchi=matchi
                plugin.sortrows=sortrows
                plugin.best_channels=best_channels
                plugin.unit_number=unit_number
                plugin.unit_type=unit_type
                plugin.m_inds=m_inds
                plugin.tablegui = tablegui #need to keep a reference otherwide the gui is deleted by garbage collection, leading to a segfault!
                plugin.table = table
                plugin.dists = dists
                
                create_table(controller,controller2,plugin)
                
                tablegui.add_view(table)
                
                actions = Actions(tablegui,
                               name='Merge',
                               menu='Merge')                
                
                @actions.add(menu='Merge',name='Set master for selected slave',shortcut='enter')   
                def set_master(plugin=plugin,controller=controller,controller2=controller2):
                    row = np.array([cell.row() for cell in plugin.table.selectedIndexes()])
                    column = np.array([cell.column() for cell in plugin.table.selectedIndexes()])
                    if len(row)==1:
                        print("Row {} and Column {} is selected".format(row,column))   
                        plugin.table.item(row[0], column[0]).setForeground(QtGui.QColor(255,0,0))
                        #plugin.table.item(0, 0).setForeground(QtGui.QColor(0,255,0))
                        plugin.table.item(row[0], plugin.matchi[plugin.sortrows[row[0]]]).setForeground(QtGui.QColor(0 ,0,0))
                        plugin.matchi[plugin.sortrows[row[0]]]=column[0]
                        plugin.table.show()
                        plugin.tablegui.show()
                    else:
                        st='Only one cell can be selected when setting master'
                        print(st)
                        plugin.tablegui.status_message=st
                        
                @actions.add(menu='Merge',name='Merge selected slaves',shortcut='m')   
                def merge_slaves_by_selection(plugin=plugin,controller=controller,controller2=controller2):
                    row = np.array([cell.row() for cell in plugin.table.selectedIndexes()])
                    column = np.array([cell.column() for cell in plugin.table.selectedIndexes()])
                    row=np.unique(row)
                    column=np.unique(column)
                    if len(column)==1 and len(row)>1:
                        merge_slaves(plugin,controller,controller2,row)
                        create_table(controller,controller2,plugin)
                        plugin.tablegui.show() 
                    else:
                        if len(column)>1:
                            st='Only one master can be selected when merging slaves'
                        elif len(row)==1:
                            st='At least two slaves must be selected to merge slaves'
                        else:
                            st='Unknown slave merging problem'
                        print(st)
                        plugin.tablegui.status_message=st                        
                        
                def merge_slaves_by_array(plugin,controller,controller2,merge_matchis):
                    from PyQt4.QtCore import pyqtRemoveInputHook
                    from pdb import set_trace
                    pyqtRemoveInputHook()
                    set_trace() 
                    for merge_matchi in merge_matchis:
                        row=np.where(plugin.matchi[plugin.sortrows]==merge_matchi)[0]     
                        merge_slaves(plugin,controller,controller2,row)
                    
                    create_table(controller,controller2,plugin)
                    plugin.tablegui.show() 
                    
                def merge_slaves(plugin,controller,controller2,row):
                    controller2.supervisor.merge(controller2.supervisor.clustering.cluster_ids[plugin.sortrows[row]].tolist())
                    assign_matchi=plugin.matchi[plugin.sortrows[row[0]]]
                    plugin.matchi=np.delete(plugin.matchi,plugin.sortrows[row], axis=0)
                    plugin.matchi=np.append(plugin.matchi,assign_matchi)
                    controller2.mean_waveforms=np.delete(controller2.mean_waveforms,plugin.sortrows[row],axis=2)
                    new_mean_waveforms=create_mean_waveforms(controller2,max_waveforms_per_cluster=100,cluster_ids=controller2.supervisor.clustering.cluster_ids[-1])
                    controller2.mean_waveforms=np.append(controller2.mean_waveforms,new_mean_waveforms,axis=2)
                    plugin.dists=np.delete(plugin.dists,plugin.sortrows[row],axis=1) 
                    plugin.dists=np.append(plugin.dists,calc_dists(controller,controller2,plugin.m_inds,s_inds=plugin.dists.shape[1]),axis=1)
                    plugin.sortrows=np.argsort(plugin.matchi)
                    
                @actions.add(menu='Merge',name='Move low-snr clusters to noise',shortcut='n')
                def move_low_snr_to_noise(plugin=plugin,controller=controller,controller2=controller2):

                    cluster_ids=controller2.supervisor.clustering.cluster_ids
                    snrs=np.zeros(cluster_ids.shape)
                    for i in range(len(cluster_ids)):
                        snrs[i]=controller2.supervisor.cluster_view._columns['snr']['func'](cluster_ids[i])
                    thresh=0.2 # for amplitude
                    thresh=0.5 # for snr
                    noise_clusts=cluster_ids[snrs<thresh]
                    
                    n_ind=[]
                    for clu in noise_clusts:
                        this_ind=np.where(controller2.supervisor.clustering.cluster_ids[plugin.sortrows]==clu)[0][0]
                        n_ind.append(this_ind)
                    
                    from PyQt4.QtCore import pyqtRemoveInputHook
                    from pdb import set_trace
                    pyqtRemoveInputHook()
                    set_trace() 
                    ind=plugin.m_inds.shape[0] 
                    plugin.matchi[plugin.sortrows[n_ind]]=ind
                    plugin.m_inds=np.insert(plugin.m_inds,ind,-2)
                    plugin.best_channels=np.insert(plugin.best_channels,ind,999)
                    plugin.unit_number=np.insert(plugin.unit_number,ind,0)
                    plugin.unit_type=np.insert(plugin.unit_type,ind,3)
                    plugin.dists=np.insert(plugin.dists,ind,-1,axis=0)
                    plugin.sortrows=np.argsort(plugin.matchi)
                    
                    create_table(controller,controller2,plugin)                                          
                    tablegui.show()
                    st='Cluster ids {} moved to noise'.format(noise_clusts)
                    print(st)
                    plugin.tablegui.status_message=st
                        
                @actions.add(menu='Merge',name='Add new unit label',shortcut='a')
                def add_unit(plugin=plugin,controller=controller,controller2=controller2):
                    chan, ok = QtGui.QInputDialog.getText(None,'Adding new unit label:', '       Channel:')     
                    if not ok:
                        return
                    try:
                        chan=int(chan)
                    except:
                        plugin.tablegui.status_message='Error inputting channel'
                        return
                    nums=plugin.unit_number[plugin.best_channels==int(chan)]
                    if len(nums)==0:
                        next_unit_num=1
                    else:
                        next_unit_num=int(nums.max())+1
                    dlg =  QtGui.QInputDialog(None)                 
                    dlg.setInputMode( QtGui.QInputDialog.TextInput) 
                    dlg.setTextValue('{}'.format(next_unit_num))
                    dlg.setLabelText("Unit number:")  
                    dlg.resize(300,300)
                    #dlg.mainLayout = QtGui.QVBoxLayout()
                    #dlg.setLayout(dlg.mainLayout)                             
                    b1 = QtGui.QRadioButton("SU",dlg)
                    b2 = QtGui.QRadioButton("MU",dlg)
                    b1.move(100,0)
                    b2.move(150,0)
                    b1.setChecked(True)
                    ok = dlg.exec_()                                
                    unit_number = dlg.textValue()
                    if not ok:
                        return
                    try:
                        unit_number=int(unit_number)
                    except:
                        plugin.tablegui.status_message='Error inputting unit number'
                        return
                    if b1.isChecked():
                        unit_type=1
                    elif b2.isChecked():
                        unit_type=2
                    else:
                        plugin.tablegui.status_message('Error getting unit type, must have checked either SU or MU')
                        return
                    below_inds=np.logical_and(plugin.unit_type==unit_type,plugin.best_channels<=chan).nonzero()[0]
                    if below_inds.shape[0]==0:
                        below_inds=plugin.unit_type==unit_type
                        below_inds=below_inds.nonzero()[0]
                    ind=below_inds[-1]+1 
                    plugin.m_inds=np.insert(plugin.m_inds,ind,-1)
                    plugin.matchi[plugin.matchi>=ind]+=1
                    plugin.best_channels=np.insert(plugin.best_channels,ind,chan)
                    plugin.unit_number=np.insert(plugin.unit_number,ind,unit_number)
                    plugin.unit_type=np.insert(plugin.unit_type,ind,unit_type)
                    plugin.dists=np.insert(plugin.dists,ind,-1,axis=0)
                    create_table(controller,controller2,plugin)
                                          
                    tablegui.show()
                    
                @actions.add(menu='Merge',name='Save cluster associations',alias='sca')   
                def save_cluster_associations(plugin=plugin,controller=controller,controller2=controller2):
                    from PyQt4.QtCore import pyqtRemoveInputHook
                    from pdb import set_trace
                    pyqtRemoveInputHook()
                    set_trace() 
                    un_matchi,counts=np.unique(plugin.matchi, return_index=False, return_inverse=False, return_counts=True)                    
                    rmi=np.where(plugin.unit_type[un_matchi]==3)[0]
                    if(len(rmi)>0):
                        un_matchi=np.delete(un_matchi,rmi)
                        counts=np.delete(counts,rmi)
                    if np.any(counts>1):
                        msgBox = QtGui.QMessageBox()
                        msgBox.setText('There are {} master clusters that are about '
                        'to be assigned multiple slave clusters. If this slave will '
                        'be used as a master for an addional merge, in most cases '
                        'slave clusters that share the same master match should be '
                        'merged.'
                        .format(np.sum(counts>1)))
                        msgBox.setInformativeText('Do you want to automatically do these merges?')
                        msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)
                        msgBox.setDefaultButton(QtGui.QMessageBox.Yes)
                        ret = msgBox.exec_()
                        if ret == QtGui.QMessageBox.Yes:
                            merge_slaves_by_array(plugin,controller,controller2,un_matchi[counts>1])
                            msgBox = QtGui.QMessageBox()
                            msgBox.setText('Merges done. Not saving yet! Check to see that everything is okay and then save.')
                            msgBox.exec_()
                            return
                        elif ret == QtGui.QMessageBox.No:
                            pass
                        else:
                            return
                    # assign labels to slave phy's clusters based on master phy's labels
                    good_clusts=controller2.supervisor.clustering.cluster_ids[plugin.sortrows[plugin.unit_type[plugin.matchi[plugin.sortrows]] == 1]].tolist()
                    controller2.supervisor.move('good',good_clusts)
                    mua_clusts=controller2.supervisor.clustering.cluster_ids[plugin.sortrows[plugin.unit_type[plugin.matchi[plugin.sortrows]] == 2]].tolist()
                    controller2.supervisor.move('mua',mua_clusts)                      
                    mua_clusts=controller2.supervisor.clustering.cluster_ids[plugin.sortrows[plugin.unit_type[plugin.matchi[plugin.sortrows]] == 3]].tolist()
                    controller2.supervisor.move('noise',mua_clusts)                       

                    #save both master and slave  
                    controller.supervisor.save()
                    controller2.supervisor.save()
                    
                    #save associations                    
                    create_tsv(op.join(controller.model.dir_path,'cluster_names.tsv'),
                        controller.supervisor.clustering.cluster_ids[plugin.m_inds[~np.in1d(plugin.m_inds,(-1,-2))]],
                        plugin.unit_type[~np.in1d(plugin.m_inds,(-1,-2))],
                        plugin.best_channels[~np.in1d(plugin.m_inds,(-1,-2))],
                        plugin.unit_number[~np.in1d(plugin.m_inds,(-1,-2))])
                    create_tsv(op.join(controller2.model.dir_path,'cluster_names.tsv'),
                        controller2.supervisor.clustering.cluster_ids[plugin.sortrows],
                        plugin.unit_type[plugin.matchi[plugin.sortrows]],
                        plugin.best_channels[plugin.matchi[plugin.sortrows]],
                        plugin.unit_number[plugin.matchi[plugin.sortrows]])        
                    with open(op.join(controller.model.dir_path,'Merged_Files.txt'), 'a') as text_file:
                        text_file.write('{} on {}\n'.format(controller2.model.dir_path,time.strftime('%c')))
                    plugin.tablegui.status_message='Saved clusted associations'
                    print('Saved clusted associations')
                def create_tsv(filename,cluster_id,unit_type,channel,unit_number):
                    if sys.version_info[0] < 3:
                        file = open(filename, 'wb')
                    else:
                        file = open(filename, 'w', newline='')
                    with file as f:
                        writer = csv.writer(f, delimiter='\t')
                        writer.writerow(['cluster_id', 'unit_type', 'chan', 'unit_number'])
                        for i in range(len(cluster_id)):
                            writer.writerow([cluster_id[i], unit_type[i],channel[i],unit_number[i]])

                
                        

                tablegui.show()
                

                
                
                    