# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions.ToggleLight.ToggleLight import ToggleLight

class HomeBridgePlugin(PluginBase):
    def __init__(self):
        super().__init__()

        ## Register actions
        self.toggle_light_holder = ActionHolder(
            plugin_base = self,
            action_base = ToggleLight,
            action_id = "ethanb_HomeBridge::ToggleLight",
            action_name = "Toggle Light",
        )
        self.add_action_holder(self.toggle_light_holder)

        # Register plugin
        self.register(
            plugin_name = "HomeBridge",
            github_repo = "https://github.com/ethanb/HomeBridge-StreamController",
            plugin_version = "1.0.0",
            app_version = "1.5.0"
        )