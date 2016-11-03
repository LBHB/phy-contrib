
from phy import IPlugin

class TraceViewUpdate(IPlugin):
    def attach_to_controller(self, c):
        @c.connect
        def on_create_gui(gui):

            @gui.connect_
            def on_select(clusters):
                tv = gui.get_view('TraceView')
                tv.set_interval(force_update=True)

