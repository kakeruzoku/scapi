from . import project
class MonitorBlock:
    def __init__(self):
        self.id: str = ""

def load_sprite(monitor_data:dict, *, _project:"project.ScratchProject") -> MonitorBlock:
    monitor = MonitorBlock()
    monitor.id = monitor_data.get("id", "")
    return monitor