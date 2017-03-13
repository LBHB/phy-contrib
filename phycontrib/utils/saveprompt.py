# -*- coding: utf-8 -*-

"""Save prompt plugin."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from phy.gui.qt import _prompt, _show_box

from phy import IPlugin


#------------------------------------------------------------------------------
# Plugin
#------------------------------------------------------------------------------

class SavePromptPlugin(IPlugin):
    def attach_to_controller(self, controller):
        @controller.connect
        def on_create_gui(gui):
            @gui.connect_
            def on_close():
                # Show save prompt if an action was done.
                if len(controller.supervisor._global_history) <= 1:
                    return
                b = _prompt("Do you want to save your modifications "
                            "before quitting?",
                            buttons=['save', 'cancel', 'close'],
                            title='Save')
                r = _show_box(b)
                if r == 'save':
                    controller.supervisor.save()
                elif r == 'cancel':
                    return False
                elif r == 'close':
                    return
