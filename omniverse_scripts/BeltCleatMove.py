import carb
import carb.settings 
import omni.usd

from pxr import Gf, UsdGeom
from omni.behavior.scripting.core import BehaviorScript


class Beltcleatmove(BehaviorScript):

    # ==========================================
    # UI PROPERTIES
    # ==========================================
    is_active: bool = True
    parent_path: str = "/World/Cleats"
    speed: float = 0.5

    def on_init(self):
        self.cleats = []
        # Updated Y coordinates
        self.start_y = 232.66544
        self.end_y = -1977.33462
        self.belt_length = self.end_y - self.start_y
        
        # Calculate which way we are moving (-1 for backwards, 1 for forwards)
        self.direction = 1 if self.belt_length > 0 else -1

    def on_play(self):
        self.cleats.clear()

        if not self.stage:
            carb.log_error("Could not find USD stage.")
            return

        # FIXED: Starts at 1 and stops at 13 to match your Outliner!
        for i in range(1, 14):
            prim_path = f"{self.parent_path}/Cleat_{i:02d}"
            prim = self.stage.GetPrimAtPath(prim_path)

            if not prim.IsValid():
                carb.log_warn(f"Animator could not find prim: {prim_path}")
                continue

            xform = UsdGeom.Xformable(prim)
            translate_op = None

            for op in xform.GetOrderedXformOps():
                if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                    translate_op = op
                    break

            if translate_op is None:
                translate_op = xform.AddTranslateOp()

            pos = translate_op.Get()

            if pos is None:
                # Set the starting position using start_y on the Y-axis
                pos = Gf.Vec3d(0.0, self.start_y, 0.0)
                translate_op.Set(pos)

            self.cleats.append(
                {
                    "op": translate_op,
                    "x": pos[0],
                    "y": pos[1],
                    "z": pos[2],
                }
            )

        carb.log_info(f"Cached {len(self.cleats)} conveyor cleats.")

    def on_update(self, current_time: float, delta_time: float):

        if not self.is_active or not self.cleats:
            return

        # ==========================================
        # READ LIVE PLC SPEED FROM CARB SETTINGS
        # ==========================================
        settings = carb.settings.get_settings()
        self.speed = settings.get_as_float("/plc_live_data/belt_speed")

        # SAFETY CLAMP: If the speed is 0 (E-Stop or PLC Stopped), freeze in place!
        if self.speed is None or abs(self.speed) < 0.0001:
            return

        # Calculate movement delta and force it to move in the correct direction
        base_speed = abs(self.speed * delta_time * 500.0)
        speed_dt = base_speed * self.direction
        
        start_y = self.start_y
        belt_length = self.belt_length

        for cleat in self.cleats:
            
            # Apply the directional speed to the Y axis
            y = cleat["y"] + speed_dt

            # Fast wrap-around using modulo
            y = ((y - start_y) % belt_length) + start_y

            cleat["y"] = y

            # Apply the new Y value, keeping X and Z exactly as they were
            cleat["op"].Set(
                Gf.Vec3d(
                    cleat["x"],
                    y,
                    cleat["z"]
                )
            )