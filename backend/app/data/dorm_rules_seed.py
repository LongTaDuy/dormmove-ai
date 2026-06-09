"""Generic dorm rule warnings.

Exports ``GENERIC_DORM_RULES``: a list of plain dicts describing common
residence-hall policies. These are conservative, school-agnostic warnings used
by the risk agent. Each entry uses a consistent shape::

    {
        "rule_id": str,            # stable identifier
        "title": str,              # short human label
        "risk": DormRuleRisk,      # value (as string) from the enum
        "keywords": list[str],     # terms used to match items / messages
        "warning": str,            # explanation shown to the student
    }

The ``risk`` value mirrors :class:`app.models.schemas.DormRuleRisk` and is
stored as its string value to keep this seed dependency-light and easy to
serialize.
"""

from __future__ import annotations

from app.models.schemas import DormRuleRisk

GENERIC_DORM_RULES: list[dict] = [
    {
        "rule_id": "candles-incense",
        "title": "Candles & incense",
        "risk": DormRuleRisk.often_prohibited.value,
        "keywords": ["candle", "incense", "open flame", "wax warmer"],
        "warning": "Open-flame items like candles and incense are banned in most dorms as a fire hazard.",
    },
    {
        "rule_id": "hot-plates",
        "title": "Hot plates & open-coil cooking",
        "risk": DormRuleRisk.often_prohibited.value,
        "keywords": ["hot plate", "hotplate", "open coil", "electric grill", "deep fryer"],
        "warning": "Open-coil cookers and hot plates are commonly prohibited; use approved appliances only.",
    },
    {
        "rule_id": "space-heaters",
        "title": "Space heaters",
        "risk": DormRuleRisk.often_prohibited.value,
        "keywords": ["space heater", "heater", "radiant heater"],
        "warning": "Portable space heaters are frequently banned due to fire risk and power draw.",
    },
    {
        "rule_id": "halogen-lamps",
        "title": "Halogen lamps",
        "risk": DormRuleRisk.often_prohibited.value,
        "keywords": ["halogen", "halogen lamp", "torchiere"],
        "warning": "Halogen and torchiere lamps run hot and are prohibited in many residence halls.",
    },
    {
        "rule_id": "extension-cords",
        "title": "Non-surge extension cords",
        "risk": DormRuleRisk.check_rules.value,
        "keywords": ["extension cord", "power cord", "daisy chain"],
        "warning": "Many dorms require UL-listed surge protectors and ban plain extension cords or daisy-chaining.",
    },
    {
        "rule_id": "wall-damage",
        "title": "Wall damage from mounting",
        "risk": DormRuleRisk.check_rules.value,
        "keywords": ["nail", "screw", "tape", "adhesive", "mount", "tack"],
        "warning": "Avoid nails/screws and aggressive tape; use removable adhesive to prevent damage charges.",
    },
    {
        "rule_id": "personal-routers",
        "title": "Personal routers & access points",
        "risk": DormRuleRisk.check_rules.value,
        "keywords": ["router", "wifi", "access point", "wireless printer", "mesh"],
        "warning": "Personal routers can interfere with campus Wi-Fi and are often disallowed.",
    },
    {
        "rule_id": "mini-fridge-size",
        "title": "Mini fridge size limits",
        "risk": DormRuleRisk.check_rules.value,
        "keywords": ["mini fridge", "refrigerator", "fridge"],
        "warning": "Mini fridges usually must be under a size/wattage limit (often ~4.0 cu ft); confirm before buying.",
    },
    {
        "rule_id": "microwave-wattage",
        "title": "Microwave wattage limits",
        "risk": DormRuleRisk.check_rules.value,
        "keywords": ["microwave"],
        "warning": "Some dorms cap microwave wattage or only allow approved micro-fridge units.",
    },
    {
        "rule_id": "pets",
        "title": "Pets",
        "risk": DormRuleRisk.often_prohibited.value,
        "keywords": ["pet", "dog", "cat", "hamster", "reptile"],
        "warning": "Pets other than small fish are typically prohibited without an approved accommodation.",
    },
    {
        "rule_id": "alcohol-underage",
        "title": "Alcohol (underage)",
        "risk": DormRuleRisk.often_prohibited.value,
        "keywords": ["alcohol", "beer", "wine", "liquor", "mini bar"],
        "warning": "Alcohol is prohibited for students under 21 and is restricted even in some upper-class housing.",
    },
    {
        "rule_id": "smoking-vaping",
        "title": "Smoking & vaping",
        "risk": DormRuleRisk.often_prohibited.value,
        "keywords": ["smoke", "smoking", "vape", "vaping", "cigarette", "tobacco"],
        "warning": "Most campuses are smoke- and vape-free, including inside residence halls.",
    },
    {
        "rule_id": "string-lights",
        "title": "String / LED lights",
        "risk": DormRuleRisk.check_rules.value,
        "keywords": ["string lights", "led lights", "fairy lights", "neon sign"],
        "warning": "Certain string or neon lights are restricted; look for dorm-safe, low-heat options.",
    },
    {
        "rule_id": "weapons",
        "title": "Weapons & sharp tools",
        "risk": DormRuleRisk.often_prohibited.value,
        "keywords": ["weapon", "knife", "firearm", "gun", "machete"],
        "warning": "Weapons (including large knives) are banned in essentially all student housing.",
    },
    {
        "rule_id": "lofting-furniture",
        "title": "Lofting & extra furniture",
        "risk": DormRuleRisk.check_rules.value,
        "keywords": ["loft", "bed riser", "extra furniture", "futon", "couch"],
        "warning": "Bed lofting kits and large furniture must meet dorm rules; confirm allowed riser heights.",
    },
]
