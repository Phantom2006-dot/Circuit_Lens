"""Human-readable organization for the 61 ElectroCom61 component labels.

The model predicts observed visual labels. This taxonomy groups those labels for
inspection and topology reasoning; it does not turn a visual label into an exact
manufacturer part identification.
"""
from __future__ import annotations


ELECTROCOM61_LABELS = [
    "1-5-Volt-Battery", "3-3-Volt-Battery", "7-Segment-Display", "9-Volt-Battery", "Arduino-Mega", "Arduino-Nano", "Arduino-Uno", "BJT-Transistor", "Bluetooth-Module", "Breadboard", "Bridge-Rectifier", "Buck-Converter", "Buzzer", "Capacitor-10mf", "Capacitor-470mf", "DC-Motor", "Diode", "ESP32", "ESP32-CAM", "FT-232-USB-Serial-Module", "Film-Capacitor", "Fuse", "Fuse-Base", "GSM-Module", "Gas-Sensor", "Heat-Sink", "High-Voltage-Ceramic-Capacitor", "Humidity-Sensor", "IC-Base-14-Pin", "IC-Base-28-Pin", "IC-Chip", "IGBT", "IR-Sensor", "Inductor", "Keypad", "LCD-Display", "LDR-Sensor", "LED-Light", "Low-Voltage-Ceramic-Capacitor", "MLC-Capacitor", "MOSFET", "Motion-Sensor", "Motor-Driver", "NTC-Thermistor", "OLED-Display", "Pin-Header", "Push-Switch", "RFID-Scanner", "Raindrops-Module", "Relay-Module", "Resistor", "Rocker-Switch", "Servo-Motor", "Soil-Moisture-Sensor", "Sonar-Sensor", "TCRT5000", "Tact-Switch", "Taper-Potentiometer", "Trimmer-Potentiometer", "Water-Sensor", "Zener-Diode",
]

GROUPS = {
    "power": {"1-5-Volt-Battery", "3-3-Volt-Battery", "9-Volt-Battery", "Buck-Converter", "Fuse", "Fuse-Base", "Relay-Module"},
    "passive": {"Resistor", "Capacitor-10mf", "Capacitor-470mf", "Film-Capacitor", "High-Voltage-Ceramic-Capacitor", "Low-Voltage-Ceramic-Capacitor", "MLC-Capacitor", "Inductor", "NTC-Thermistor", "LDR-Sensor", "Taper-Potentiometer", "Trimmer-Potentiometer"},
    "semiconductor": {"Diode", "Zener-Diode", "Bridge-Rectifier", "BJT-Transistor", "MOSFET", "IGBT", "LED-Light", "IC-Chip", "Motor-Driver"},
    "interconnect": {"Pin-Header", "IC-Base-14-Pin", "IC-Base-28-Pin", "Breadboard"},
    "controller_module": {"Arduino-Mega", "Arduino-Nano", "Arduino-Uno", "ESP32", "ESP32-CAM", "Bluetooth-Module", "GSM-Module", "FT-232-USB-Serial-Module", "RFID-Scanner"},
    "sensor_module": {"Gas-Sensor", "Humidity-Sensor", "IR-Sensor", "Motion-Sensor", "Raindrops-Module", "Soil-Moisture-Sensor", "Sonar-Sensor", "TCRT5000", "Water-Sensor"},
    "electromechanical": {"Buzzer", "DC-Motor", "Servo-Motor", "Push-Switch", "Rocker-Switch", "Tact-Switch", "Keypad"},
    "display_support": {"7-Segment-Display", "LCD-Display", "OLED-Display", "Heat-Sink"},
}

TERMINAL_COUNTS = {
    "Resistor": 2, "Capacitor-10mf": 2, "Capacitor-470mf": 2, "Film-Capacitor": 2, "High-Voltage-Ceramic-Capacitor": 2, "Low-Voltage-Ceramic-Capacitor": 2, "MLC-Capacitor": 2, "Inductor": 2, "Diode": 2, "Zener-Diode": 2, "LED-Light": 2, "Fuse": 2, "NTC-Thermistor": 2, "LDR-Sensor": 2, "BJT-Transistor": 3, "MOSFET": 3, "IGBT": 3, "Bridge-Rectifier": 4, "Pin-Header": 4, "IC-Base-14-Pin": 14, "IC-Base-28-Pin": 28,
}


def group_for_label(label: str) -> str:
    for group, labels in GROUPS.items():
        if label in labels:
            return group
    return "other"


def terminal_count(label: str) -> int:
    return TERMINAL_COUNTS.get(label, 0)


def display_name(label: str) -> str:
    return label.replace("-", " ")
