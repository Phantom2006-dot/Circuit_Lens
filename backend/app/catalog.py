"""Curated component reference records with manufacturer documentation links.

This catalog is a practical identification aid. It never asserts that an image
alone has established an exact manufacturer part number; visual detection yields
a component family, then the UI presents the closest documented reference.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ComponentReference:
    key: str
    family: str
    manufacturer: str
    part_number: str
    package: str
    reference_value: str
    engineering_summary: str
    specifications: dict[str, str]
    datasheet_url: str
    source_title: str
    source_url: str
    application: str


CATALOG: tuple[ComponentReference, ...] = (
    ComponentReference(
        key="resistor-0603-1k",
        family="Resistor",
        manufacturer="Vishay",
        part_number="CRCW0603 1 kΩ reference",
        package="0603 / 1608 metric",
        reference_value="1 kΩ · ±1% · ±100 ppm/K",
        engineering_summary="Thick-film chip resistor reference drawn from the CRCW0603 1% E96 series.",
        specifications={"Resistance": "1 kΩ", "Tolerance": "±1%", "Temperature coefficient": "±100 ppm/K", "Series range": "10 Ω to 1 MΩ", "EIA case": "0603"},
        datasheet_url="https://www.vishay.com/doc/?20078",
        source_title="Vishay D11/CRCW0603 e3 sample-kit data sheet",
        source_url="https://www.vishay.com/doc/?20078",
        application="Bias, pull-up/pull-down, and current-limiting networks.",
    ),
    ComponentReference(
        key="transistor-2n3904",
        family="Transistor",
        manufacturer="onsemi",
        part_number="2N3904",
        package="TO-92",
        reference_value="NPN silicon transistor",
        engineering_summary="General-purpose NPN transistor; the exact device must be confirmed from board markings or a bill of materials.",
        specifications={"VCEO": "40 V", "VCBO": "60 V", "VEBO": "6 V", "Collector current": "200 mA continuous", "Power dissipation": "625 mW at 25 °C", "Temperature range": "−55 to +150 °C"},
        datasheet_url="https://www.onsemi.com/pdf/datasheet/2n3903-d.pdf",
        source_title="onsemi 2N3903 / 2N3904 General Purpose Transistors data sheet",
        source_url="https://www.onsemi.com/pdf/datasheet/2n3903-d.pdf",
        application="Low-power switching and small-signal amplification.",
    ),
    ComponentReference(
        key="diode-1n4148ws",
        family="Diode",
        manufacturer="onsemi",
        part_number="1N4148WS",
        package="SOD-323FL",
        reference_value="Fast small-signal switching diode",
        engineering_summary="Small-signal switching diode reference; polarity must be confirmed from the cathode band and circuit context.",
        specifications={"Repetitive peak reverse voltage": "75 V", "Non-repetitive peak reverse voltage": "100 V", "Continuous forward current": "150 mA", "Forward voltage": "1 V max at 10 mA", "Capacitance": "4 pF max", "Reverse-recovery time": "4 ns max"},
        datasheet_url="https://www.onsemi.com/pdf/datasheet/1n4148ws-d.pdf",
        source_title="onsemi 1N4148WS / 1N4448WS / 1N914BWS Small Signal Diodes data sheet",
        source_url="https://www.onsemi.com/pdf/datasheet/1n4148ws-d.pdf",
        application="High-speed signal steering, clamping, and switching.",
    ),
    ComponentReference(
        key="capacitor-c0603c104k5ractu",
        family="Capacitor",
        manufacturer="KEMET / YAGEO",
        part_number="C0603C104K5RACTU",
        package="0603 / 1608 metric",
        reference_value="0.1 µF · ±10% · 50 VDC · X7R",
        engineering_summary="Class-II X7R MLCC reference. Capacitance changes with DC bias and temperature; use the manufacturer model for design verification.",
        specifications={"Capacitance": "0.1 µF", "Tolerance": "±10%", "Rated voltage": "50 VDC", "Dielectric": "X7R", "Temperature range": "−55 to +125 °C", "Insulation resistance": "5 GΩ", "Dimensions": "1.6 × 0.8 × 0.8 mm"},
        datasheet_url="https://search.kemet.com/component-documentation/download/specsheet/C0603C104K5RACTU",
        source_title="KEMET C0603C104K5RACTU component specification",
        source_url="https://search.kemet.com/component-documentation/download/specsheet/C0603C104K5RACTU",
        application="Local decoupling and noise suppression.",
    ),
    ComponentReference(
        key="regulator-l7805cv",
        family="Voltage Regulator",
        manufacturer="STMicroelectronics",
        part_number="L7805CV",
        package="TO-220",
        reference_value="Fixed positive 5 V regulator",
        engineering_summary="Three-terminal linear-regulator reference for low-noise 5 V rails; thermal design depends on input voltage and load current.",
        specifications={"Output voltage": "5 V fixed", "Output current": "Up to 1.5 A", "Maximum input voltage": "35 V", "Dropout": "2 V typical at 1 A", "Package": "TO-220"},
        datasheet_url="https://estore.st.com/en/l7805cv-cpn.html",
        source_title="STMicroelectronics L7805CV product page",
        source_url="https://estore.st.com/en/l7805cv-cpn.html",
        application="On-board regulated 5 V supplies.",
    ),
    ComponentReference(
        key="header-0022232041",
        family="Pin Header",
        manufacturer="Molex",
        part_number="0022232041",
        package="1 × 4 through-hole, vertical",
        reference_value="4-position, 2.54 mm pitch header",
        engineering_summary="Board-interconnect reference. Pin count and pitch are visual cues, but the exact series must be verified mechanically.",
        specifications={"Positions": "4", "Pitch": "2.54 mm / 0.100 in", "Mounting": "Through-hole", "Orientation": "Vertical", "Contact style": "Male pin"},
        datasheet_url="https://www.molex.com/en-us/products/part-detail/22232041",
        source_title="Molex 0022232041 product page",
        source_url="https://www.molex.com/en-us/products/part-detail/22232041",
        application="Board-to-wire and board-to-board interconnects.",
    ),
)


def references_for_family(family: str) -> list[dict[str, object]]:
    return [asdict(record) for record in CATALOG if record.family == family]


def all_references() -> list[dict[str, object]]:
    return [asdict(record) for record in CATALOG]
