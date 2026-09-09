"""
===============================================================================
Secure Smart Factory Digital Twin - OPC UA & AI Bridge
===============================================================================
Description:
    Omniverse BehaviorScript handling real-time telemetry ingestion from a
    Siemens S7-1500 PLC over encrypted OPC UA (Basic256Sha256 / X.509 certs).
    Executes real-time Scikit-Learn inference models for Jam, Anomaly, and 
    Predictive Maintenance (PdM) diagnostics, and writes alarm states back to PLC.

Author: Master's Thesis Portfolio Framework
License: MIT
===============================================================================
"""

import os
import asyncio
import logging
import warnings
import numpy as np

# Omniverse Core APIs
import carb
import carb.settings
import omni.ui as ui
from omni.behavior.scripting.core import BehaviorScript

# Async OPC UA Library
from asyncua import Client, ua

# Mute noisy asyncua protocol logs
logging.getLogger("asyncua").setLevel(logging.CRITICAL)

# Omniverse PIP Package Injection
import omni.kit.pipapi
omni.kit.pipapi.install("scikit-learn")
omni.kit.pipapi.install("joblib")
import joblib

warnings.filterwarnings("ignore", message="X does not have valid feature names")


class PlcVariables:
    """In-memory data store for live PLC sensor states, HMI sliders, and local timers."""
    def __init__(self):
        # Sensor & HMI Telemetry
        self.base_weight = 0.0
        self.final_belt_speed = 0.0
        self.weight = 0.0      
        self.friction = 0.0
        self.hopper_level = 0.0
        self.mass_flow_rate = 0.0        
        
        # Machine Actuator States
        self.vibrator_status = False
        self.vibrator_damage = False 
        
        # Real-time Condition Timers (Seconds)
        self.time_jam = 0.0
        self.time_anomaly = 0.0
        self.time_maintenance = 0.0
        
        # Diagnostic Alarm Flags
        self.jam_alarm = False
        self.maintenance_alarm = False
        self.anomaly_alarm = False

# Global state container
global_vars = PlcVariables()


class SubHandler:
    """Asynchronous OPC UA Subscription DataChange Handler."""
    def datachange_notification(self, node, val, data):
        node_id_str = str(node.nodeid.Identifier)
        settings = carb.settings.get_settings()
        
        # Process Sensor Reads & Inject Live States into Omniverse carb.settings
        if "base_olives_weight_onBelt_real" in node_id_str:
            global_vars.base_weight = float(val)
        elif "final_belt_speed" in node_id_str:
            global_vars.final_belt_speed = float(val)
            settings.set("/plc_live_data/belt_speed", float(val)) 
        elif "Final_olives_weight_onBelt_real" in node_id_str:
            global_vars.weight = float(val)
        elif "friction_extra_weight_real" in node_id_str:
            global_vars.friction = float(val)
        elif "hopper_level" in node_id_str:
            global_vars.hopper_level = float(val)
            settings.set("/plc_live_data/hopper_level", float(val))
        elif "mass_flow_rate" in node_id_str:
            global_vars.mass_flow_rate = float(val)
        elif "vibrator_status" in node_id_str:
            global_vars.vibrator_status = bool(val)
        elif "vibrator_damage" in node_id_str:
            global_vars.vibrator_damage = bool(val)
            
        # Alarm Synchronisation
        elif "jam_prediction_alarm" in node_id_str:
            global_vars.jam_alarm = bool(val)
            settings.set("/plc_live_data/jam_alarm", bool(val))
        elif "maintaince_alarm" in node_id_str:
            global_vars.maintenance_alarm = bool(val)
            settings.set("/plc_live_data/maintenance_alarm", bool(val))
        elif "anomaly_detection_alarm" in node_id_str:
            global_vars.anomaly_alarm = bool(val)
            settings.set("/plc_live_data/anomaly_alarm", bool(val))


class Plcconnector(BehaviorScript):
    """Main Omniverse BehaviorScript connecting PLC, AI, and USD Stage."""
    
    def on_init(self):
        self._window = None
        self.client = None
        
        # Default Server Configuration (Overridden by environment or local setup)
        self.plc_url = os.getenv("OPC_UA_SERVER_URL", "opc.tcp://127.0.0.1:4840")  
        
        # Relative Path Resolution for AI Models
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "ai_diagnostics", "models", "smart_factory_ai.pkl")
        
        try:
            self.ai_models = joblib.load(model_path)
            carb.log_info("Smart Factory AI Diagnostics successfully loaded!")
        except Exception as e:
            carb.log_error(f"AI Diagnostics Model Load Failed: {e}")
            self.ai_models = None

    def on_play(self):
        self._build_ui()
        global_vars.time_jam = 0.0
        global_vars.time_anomaly = 0.0
        global_vars.time_maintenance = 0.0

    def on_stop(self):
        if self._window:
            self._window.visible = False
            self._window = None
        
    def on_destroy(self):
        if self.client is not None:
            asyncio.ensure_future(self._disconnect_plc())

    def on_update(self, current_time: float, delta_time: float):
        if self._window and self.client:
            
            # 1. Update Jam Timer Condition
            if global_vars.weight < 50.0 and not global_vars.vibrator_damage:
                global_vars.time_jam += delta_time
            else:
                global_vars.time_jam = 0.0

            # 2. Update Anomaly Timer Condition
            if global_vars.weight < 50.0 and global_vars.vibrator_damage:
                global_vars.time_anomaly += delta_time
            else:
                global_vars.time_anomaly = 0.0

            # 3. Update Maintenance Timer Condition
            if 90.0 <= global_vars.base_weight <= 100.0 and global_vars.friction > 20.0:
                global_vars.time_maintenance += delta_time
            else:
                global_vars.time_maintenance = 0.0

            # 4. Enforce Local Actuator State Rules
            global_vars.vibrator_status = (global_vars.weight < 50.0) and not global_vars.vibrator_damage
            carb.settings.get_settings().set("/plc_live_data/vibrator_status", global_vars.vibrator_status)

            # 5. Execute Real-Time Machine Learning Diagnostics
            self._run_ai_predictions()

            # 6. Refresh UI Dashboard Elements
            self._base_wt_lbl.text = f"Base Weight Input: {global_vars.base_weight:.1f} kg"
            self._speed_lbl.text = f"Belt Speed: {global_vars.final_belt_speed:.2f} m/s"
            self._weight_lbl.text = f"Total Final Mass: {global_vars.weight:.1f} kg"
            self._frict_lbl.text = f"Friction Load: {global_vars.friction:.1f} kg"
            self._hopper_lbl.text = f"Hopper Level: {global_vars.hopper_level:.1f} %"
            self._flow_lbl.text = f"Mass Flow Rate: {global_vars.mass_flow_rate:.1f} units/s"
            
            self._vibe_lbl.text = f"Vibrator Status: {'ACTIVE' if global_vars.vibrator_status else 'INACTIVE'}"
            self._dmg_lbl.text = f"Vibrator Fault: {'DAMAGE DETECTED' if global_vars.vibrator_damage else 'NORMAL'}"
            
            self._timer_lbl.text = (f"T-Jam: {global_vars.time_jam:.1f}s | "
                                    f"T-Anom: {global_vars.time_anomaly:.1f}s | "
                                    f"T-Maint: {global_vars.time_maintenance:.1f}s")
            
            self._jam_lbl.style = {"color": 0xFF0000FF if global_vars.jam_alarm else 0xFF00FF00}
            self._maint_lbl.style = {"color": 0xFF00AFFF if global_vars.maintenance_alarm else 0xFF00FF00}
            self._anom_lbl.style = {"color": 0xFF0000FF if global_vars.anomaly_alarm else 0xFF00FF00}

    def _run_ai_predictions(self):
        if not self.ai_models:
            return

        # Prepare 8-feature input array matching trained Scikit-Learn pipeline
        current_data = np.array([[
            global_vars.weight, 
            global_vars.mass_flow_rate, 
            int(global_vars.vibrator_damage), 
            global_vars.time_jam,
            global_vars.time_anomaly,
            global_vars.time_maintenance,
            global_vars.friction,
            global_vars.base_weight
        ]])

        jam_pred = bool(self.ai_models["jam_model"].predict(current_data)[0] == 1)
        maint_pred = bool(self.ai_models["maintenance_model"].predict(current_data)[0] == 1)
        anom_pred = bool(self.ai_models["anomaly_model"].predict(current_data)[0] == 1)

        # Write-back detected alarm flags directly to Siemens PLC tags over OPC UA
        if jam_pred != global_vars.jam_alarm:
            global_vars.jam_alarm = jam_pred
            asyncio.ensure_future(self._write_to_plc('ns=3;s="PLC_Variables"."jam_prediction_alarm"', jam_pred))

        if maint_pred != global_vars.maintenance_alarm:
            global_vars.maintenance_alarm = maint_pred
            asyncio.ensure_future(self._write_to_plc('ns=3;s="PLC_Variables"."maintaince_alarm"', maint_pred))

        if anom_pred != global_vars.anomaly_alarm:
            global_vars.anomaly_alarm = anom_pred
            asyncio.ensure_future(self._write_to_plc('ns=3;s="PLC_Variables"."anomaly_detection_alarm"', anom_pred))
    
    async def _write_to_plc(self, node_str: str, val: bool):
        if self.client:
            try:
                node = self.client.get_node(node_str)
                await node.write_value(ua.DataValue(ua.Variant(val, ua.VariantType.Boolean)))
            except Exception as e:
                carb.log_warn(f"OPC UA Write-back Error: {e}")

    def _build_ui(self):
        """Builds native Omniverse UI Dashboard Window."""
        self._window = ui.Window("Smart Factory Control Dashboard", width=370, height=540)
        with self._window.frame:
            with ui.VStack(spacing=8, margin=15):
                self._status_label = ui.Label("Status: Disconnected", style={"color": 0xFF5555FF}) 
                ui.Button("Connect to Siemens S7-1500 PLC", clicked_fn=self._on_connect_clicked, height=30)
                ui.Line()
                
                ui.Label("LIVE SENSOR TELEMETRY:", style={"font_weight": "bold", "color": 0xFFCCCCCC})
                self._base_wt_lbl = ui.Label("Base Weight Input: --")
                self._speed_lbl = ui.Label("Belt Speed: --")
                self._weight_lbl = ui.Label("Total Final Mass: --")
                self._frict_lbl = ui.Label("Friction Load: --")
                self._hopper_lbl = ui.Label("Hopper Level: --")
                self._flow_lbl = ui.Label("Mass Flow Rate: --")
                
                ui.Line()
                ui.Label("MACHINE HARDWARE STATUS:", style={"font_weight": "bold", "color": 0xFFCCCCCC})
                self._vibe_lbl = ui.Label("Vibrator Status: --")
                self._dmg_lbl = ui.Label("Vibrator Fault: --")
                self._timer_lbl = ui.Label("Diagnostic Timers: --")
                
                ui.Line()
                ui.Label("PREDICTIVE AI DIAGNOSTICS:", style={"font_weight": "bold", "color": 0xFFCCCCCC})
                self._jam_lbl = ui.Label("JAM DETECTED", style={"color": 0xFF888888})
                self._maint_lbl = ui.Label("MAINTENANCE REQUIRED", style={"color": 0xFF888888})
                self._anom_lbl = ui.Label("ANOMALY DETECTED", style={"color": 0xFF888888})

    def _on_connect_clicked(self):
        self._status_label.text = "Status: Establishing Encrypted Handshake..."
        self._status_label.style = {"color": 0xFF00FFFF} 
        asyncio.ensure_future(self._connect_to_plc())

    async def _connect_to_plc(self):
        """Establishes Basic256Sha256 SignAndEncrypt connection using custom X.509 certificates."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        certs_dir = os.path.join(base_dir, "certs")
        
        # Certificate and Key configuration
        cert_path = os.path.join(certs_dir, "PyClient_X509_Certificate.der")  
        key_path = os.path.join(certs_dir, "PyClient_X509_Certificate.pem")    
        
        self.client = Client(url=self.plc_url)

        # OVERRIDE APPLICATION URI to solve Siemens S7-1500 BadCertificateUriInvalid
        self.client.application_uri = "urn:SIMATIC.S7-1500.OPC-UA.Application:PLC_1"

        security_string = f"Basic256Sha256,SignAndEncrypt,{cert_path},{key_path}"

        try:
            await self.client.set_security_string(security_string)
            await self.client.connect()
            
            self._status_label.text = "Status: Securely Connected (Basic256Sha256)"
            self._status_label.style = {"color": 0xFF55FF55}
            
            handler = SubHandler()
            self.sub = await self.client.create_subscription(100, handler)

            # Subscribe to S7-1500 PLC DB Tags
            nodes_to_subscribe = [
                self.client.get_node('ns=3;s="PLC_Variables"."base_olives_weight_onBelt_real"'),
                self.client.get_node('ns=3;s="PLC_Variables"."final_belt_speed"'),
                self.client.get_node('ns=3;s="PLC_Variables"."Final_olives_weight_onBelt_real"'),
                self.client.get_node('ns=3;s="PLC_Variables"."friction_extra_weight_real"'),
                self.client.get_node('ns=3;s="PLC_Variables"."hopper_level"'),
                self.client.get_node('ns=3;s="PLC_Variables"."mass_flow_rate"'),
                self.client.get_node('ns=3;s="PLC_Variables"."vibrator_status"'),
                self.client.get_node('ns=3;s="PLC_Variables"."vibrator_damage"'),
                self.client.get_node('ns=3;s="PLC_Variables"."jam_prediction_alarm"'),
                self.client.get_node('ns=3;s="PLC_Variables"."maintaince_alarm"'),
                self.client.get_node('ns=3;s="PLC_Variables"."anomaly_detection_alarm"')
            ]
            await self.sub.subscribe_data_change(nodes_to_subscribe)
        except Exception as e:
            carb.log_error(f"Secure PLC Connection Failed: {e}")
            self._status_label.text = "Status: Secure Connection Failed"
            self._status_label.style = {"color": 0xFF0000FF}
            self.client = None 

    async def _disconnect_plc(self):
        if self.client is not None:
            try:
                if hasattr(self, 'sub') and self.sub is not None:
                    try:
                        await self.sub.delete()
                    except: pass
                await asyncio.sleep(0.2) 
                await self.client.disconnect()
            except: pass
            finally:
                self.client = None