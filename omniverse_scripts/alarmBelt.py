from omni.behavior.scripting.core import BehaviorScript
from pxr import Gf
import carb.settings

class Alarmbelt(BehaviorScript):
    def on_init(self):
        self.timer = 0.0
        self.blink_interval = 0.3  # Switches every 0.3 seconds for a fast alarm effect
        self.is_red = False
        
        # Hardcoded path exactly as requested
        self._prim_path = "/World/Looks/OmniPBR_Belt/Shader"
        self.attr_name = "inputs:diffuse_color_constant"

    def on_update(self, current_time: float, delta_time: float):
        if not self.stage:
            return

        # 1. Grab the specific shader using your absolute path
        shader_prim = self.stage.GetPrimAtPath(self._prim_path)
        if not shader_prim.IsValid():
            return
            
        attr = shader_prim.GetAttribute(self.attr_name)  # type: ignore
        if not attr:
            return

        # 2. Check the live PLC status
        settings = carb.settings.get_settings()
        self.is_maintenance = settings.get_as_bool("/plc_live_data/maintenance_alarm")

        # 3. If NO alarm, force the belt back to standard Green and reset timer
        if not self.is_maintenance:
            attr.Set(Gf.Vec3f(0.0, 1.0, 0.0))
            self.timer = 0.0
            self.is_red = False
            return

        # 4. If there IS an alarm, run the fast 0.3s blink cycle
        self.timer += delta_time
        
        if self.timer >= self.blink_interval:
            self.timer -= self.blink_interval  # Reset timer smoothly
            self.is_red = not self.is_red      # Toggle color state
            
            # Apply the colors
            if self.is_red:
                attr.Set(Gf.Vec3f(1.0, 0.0, 0.0))  # Red
            else:
                attr.Set(Gf.Vec3f(1.0, 1.0, 1.0))  # White