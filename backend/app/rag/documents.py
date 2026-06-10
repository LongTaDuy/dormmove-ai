"""Curated local dorm move-in knowledge snippets for retrieval.

These are generic planning tips and common dorm-rule themes. They do NOT
replace a school's official housing policy.
"""

from __future__ import annotations

LOCAL_DORM_KNOWLEDGE: list[dict] = [
    {
        "doc_id": "rule-candles",
        "title": "Candles and open flames",
        "source_type": "generic_rule",
        "content": (
            "Candles, incense, and open flames are commonly prohibited in dorm "
            "rooms due to fire risk. Use flameless LED alternatives instead."
        ),
        "tags": ["rules", "fire", "prohibited", "safety"],
        "risk_level": "high",
    },
    {
        "doc_id": "rule-hot-plate",
        "title": "Hot plates and coil burners",
        "source_type": "generic_rule",
        "content": (
            "Hot plates, coil burners, and exposed heating elements are often "
            "banned in residence halls. Check whether your school allows a "
            "microwave or approved cooking appliance."
        ),
        "tags": ["rules", "appliances", "prohibited", "cooking"],
        "risk_level": "high",
    },
    {
        "doc_id": "rule-air-fryer",
        "title": "Air fryers and toaster ovens",
        "source_type": "generic_rule",
        "content": (
            "Air fryers, toaster ovens, and similar countertop cooking devices "
            "may exceed wattage limits or be prohibited. Appliance rules vary "
            "by school and must be verified in official housing policy."
        ),
        "tags": ["rules", "appliances", "prohibited", "cooking"],
        "risk_level": "high",
    },
    {
        "doc_id": "rule-extension-cord",
        "title": "Extension cords vs surge protectors",
        "source_type": "generic_rule",
        "content": (
            "Many dorms restrict daisy-chained extension cords. A single surge "
            "protector with a built-in circuit breaker is usually safer than "
            "multiple cheap extension cords."
        ),
        "tags": ["rules", "electrical", "safety", "power"],
        "risk_level": "medium",
    },
    {
        "doc_id": "rule-wall-damage",
        "title": "Wall damage and mounting",
        "source_type": "generic_rule",
        "content": (
            "Nails, screws, and strong adhesives can damage walls and trigger "
            "fees. Command strips or school-approved mounting methods are "
            "typically preferred; confirm weight limits."
        ),
        "tags": ["rules", "room", "damage", "decor"],
        "risk_level": "medium",
    },
    {
        "doc_id": "rule-personal-router",
        "title": "Personal Wi-Fi routers",
        "source_type": "generic_rule",
        "content": (
            "Personal wireless routers and access points may interfere with "
            "campus networks and are often prohibited. Use the school's "
            "provided Wi-Fi or an Ethernet adapter when allowed."
        ),
        "tags": ["rules", "electronics", "network", "prohibited"],
        "risk_level": "medium",
    },
    {
        "doc_id": "rule-space-heater",
        "title": "Space heaters",
        "source_type": "generic_rule",
        "content": (
            "Portable space heaters are frequently banned because of fire risk "
            "and electrical load. Layer clothing and use approved bedding "
            "instead unless housing explicitly allows a certified model."
        ),
        "tags": ["rules", "appliances", "fire", "prohibited"],
        "risk_level": "high",
    },
    {
        "doc_id": "rule-pets",
        "title": "Pets in residence halls",
        "source_type": "generic_rule",
        "content": (
            "Most dorms prohibit pets other than approved service or support "
            "animals. Fish in small tanks are sometimes an exception—verify "
            "with housing before bringing any animal."
        ),
        "tags": ["rules", "pets", "housing", "prohibited"],
        "risk_level": "medium",
    },
    {
        "doc_id": "rule-alcohol",
        "title": "Underage alcohol and substances",
        "source_type": "generic_rule",
        "content": (
            "Alcohol, drugs, and paraphernalia violate typical dorm policies "
            "and state law for underage students. Sanctions can include "
            "housing probation or removal."
        ),
        "tags": ["rules", "alcohol", "conduct", "prohibited"],
        "risk_level": "high",
    },
    {
        "doc_id": "rule-school-specific",
        "title": "School-specific rules must be checked",
        "source_type": "generic_rule",
        "content": (
            "Prohibited appliances, wattage limits, and mounting rules differ "
            "by campus and building. Always read your school's official housing "
            "handbook before purchasing major items."
        ),
        "tags": ["rules", "policy", "disclaimer", "housing"],
        "risk_level": "low",
    },
    {
        "doc_id": "pack-laundry",
        "title": "Laundry essentials",
        "source_type": "packing_tip",
        "content": (
            "Pack detergent pods or small bottles, a mesh laundry bag, quarters "
            "or a campus card if machines require them, and a stain remover. "
            "Label your basket to avoid mix-ups in shared laundry rooms."
        ),
        "tags": ["packing", "laundry", "essentials", "checklist"],
        "risk_level": "low",
    },
    {
        "doc_id": "pack-shower-caddy",
        "title": "Shower caddy and bathroom kit",
        "source_type": "packing_tip",
        "content": (
            "A shower caddy with holes for drainage, flip-flops, and a quick-dry "
            "towel set make shared bathrooms easier. Keep toiletries in travel "
            "sizes until you know what fits your routine."
        ),
        "tags": ["packing", "bathroom", "essentials", "checklist"],
        "risk_level": "low",
    },
    {
        "doc_id": "pack-twin-xl",
        "title": "Twin XL bedding",
        "source_type": "packing_tip",
        "content": (
            "Most dorm beds require Twin XL sheets, not standard twin. Confirm "
            "mattress size before buying comforters and mattress toppers."
        ),
        "tags": ["packing", "bedding", "essentials", "checklist"],
        "risk_level": "low",
    },
    {
        "doc_id": "pack-cleaning",
        "title": "Basic cleaning supplies",
        "source_type": "packing_tip",
        "content": (
            "Bring all-purpose cleaner, disinfecting wipes, a small vacuum or "
            "dustpan, and trash bags. Shared suites may require you to maintain "
            "your own room even when bathrooms are cleaned by staff."
        ),
        "tags": ["packing", "cleaning", "essentials", "checklist"],
        "risk_level": "low",
    },
    {
        "doc_id": "pack-compact-flight",
        "title": "Compact packing for flights",
        "source_type": "logistics_tip",
        "content": (
            "Flying to campus limits luggage weight and size. Pack clothes in "
            "compression bags, ship bedding to campus if allowed, and avoid "
            "bulky decor in your checked bags."
        ),
        "tags": ["logistics", "flight", "packing", "compact", "transportation"],
        "risk_level": "low",
    },
    {
        "doc_id": "pack-buy-after-arrival",
        "title": "Buy bulky items after arrival",
        "source_type": "logistics_tip",
        "content": (
            "Mini fridges, rugs, storage towers, and desk chairs are easier to "
            "buy or rent near campus than to fly with. Coordinate with your "
            "roommate before purchasing shared bulky items."
        ),
        "tags": ["logistics", "flight", "shopping", "bulky", "roommate"],
        "risk_level": "low",
    },
    {
        "doc_id": "pack-shipping-campus",
        "title": "Shipping to campus vs home",
        "source_type": "logistics_tip",
        "content": (
            "Many schools offer mail-hold or package centers before move-in. "
            "Shipping to campus can beat flying with heavy items, but confirm "
            "delivery windows and address format with housing."
        ),
        "tags": ["logistics", "shipping", "move-in", "transportation"],
        "risk_level": "low",
    },
    {
        "doc_id": "roommate-duplicates",
        "title": "Coordinate duplicate items with roommate",
        "source_type": "roommate_tip",
        "content": (
            "Split shared purchases like mini fridges, microwaves, printers, and "
            "area rugs before move-in. One fridge and one rug per room is "
            "usually enough and saves budget."
        ),
        "tags": ["roommate", "coordination", "budget", "duplicates"],
        "risk_level": "low",
    },
    {
        "doc_id": "roommate-shared-list",
        "title": "Shared vs personal item list",
        "source_type": "roommate_tip",
        "content": (
            "Agree on who brings cleaning supplies, a TV, game console, and "
            "kitchen extras. Mark roommate-provided items on your checklist "
            "to avoid double-buying."
        ),
        "tags": ["roommate", "coordination", "checklist", "packing"],
        "risk_level": "low",
    },
    {
        "doc_id": "budget-prioritize-essentials",
        "title": "Budget prioritization",
        "source_type": "budget_tip",
        "content": (
            "Fund bedding, toiletries, laundry supplies, and school supplies "
            "before decor and gadgets. Essentials reduce day-one stress even "
            "if optional items wait until later sales."
        ),
        "tags": ["budget", "priorities", "essentials", "shopping"],
        "risk_level": "low",
    },
    {
        "doc_id": "budget-cheaper-alternatives",
        "title": "Cheaper alternatives when over budget",
        "source_type": "budget_tip",
        "content": (
            "If estimates exceed your budget, downgrade decor, buy store-brand "
            "basics, delay non-essential electronics, and purchase bulky "
            "furniture used or after arrival."
        ),
        "tags": ["budget", "savings", "shopping", "priorities"],
        "risk_level": "low",
    },
    {
        "doc_id": "budget-track-shared",
        "title": "Track shared purchases with roommate",
        "source_type": "budget_tip",
        "content": (
            "Split shared item costs upfront and record who paid for what. "
            "Shared spreadsheets prevent disputes over fridges, rugs, and "
            "subscription services."
        ),
        "tags": ["budget", "roommate", "coordination", "shared"],
        "risk_level": "low",
    },
    {
        "doc_id": "logistics-documents",
        "title": "Documents, ID, and insurance",
        "source_type": "logistics_tip",
        "content": (
            "Keep housing paperwork, student ID, health insurance card, and "
            "emergency contacts in a folder you carry on move-in day. Upload "
            "copies to secure cloud storage as backup."
        ),
        "tags": ["logistics", "documents", "move-in", "essentials"],
        "risk_level": "medium",
    },
    {
        "doc_id": "logistics-move-in-day",
        "title": "Move-in day flow",
        "source_type": "logistics_tip",
        "content": (
            "Arrive during your assigned window, bring a dolly or cart if "
            "allowed, and label boxes by room area. Elevators and loading zones "
            "fill quickly on peak move-in hours."
        ),
        "tags": ["logistics", "move-in", "timeline", "packing"],
        "risk_level": "low",
    },
    {
        "doc_id": "logistics-early-orders",
        "title": "Order shipped items early",
        "source_type": "logistics_tip",
        "content": (
            "Items with multi-day shipping should be ordered at least two "
            "weeks before move-in when possible. Track packages and confirm "
            "campus mail center hours."
        ),
        "tags": ["logistics", "shipping", "timeline", "shopping"],
        "risk_level": "medium",
    },
    {
        "doc_id": "safety-power-strip",
        "title": "Power strip safety",
        "source_type": "safety_tip",
        "content": (
            "Use UL-listed surge protectors with overload shutoff. Do not run "
            "cords under rugs, overload a single outlet, or plug high-wattage "
            "heaters into power strips."
        ),
        "tags": ["safety", "electrical", "power", "rules"],
        "risk_level": "high",
    },
    {
        "doc_id": "safety-fabric-near-heat",
        "title": "Fabric near heat sources",
        "source_type": "safety_tip",
        "content": (
            "Keep curtains, tapestries, and bedding away from radiators, "
            "halogen lamps, and cooking appliances. Fire marshals routinely "
            "flag draped fabric in dorm inspections."
        ),
        "tags": ["safety", "fire", "room", "decor"],
        "risk_level": "high",
    },
    {
        "doc_id": "safety-medication-storage",
        "title": "Medication and first-aid basics",
        "source_type": "safety_tip",
        "content": (
            "Pack a small first-aid kit, any prescription medications, and "
            "allergy remedies. Know where the nearest campus health center is "
            "before move-in weekend."
        ),
        "tags": ["safety", "health", "essentials", "packing"],
        "risk_level": "medium",
    },
    {
        "doc_id": "pack-double-room",
        "title": "Double room space planning",
        "source_type": "packing_tip",
        "content": (
            "In shared doubles, favor vertical storage, under-bed bins, and "
            "collapsible hampers. Measure closet and desk space if the housing "
            "portal provides dimensions."
        ),
        "tags": ["packing", "room", "double", "storage", "checklist"],
        "risk_level": "low",
    },
    {
        "doc_id": "pack-single-room",
        "title": "Single room flexibility",
        "source_type": "packing_tip",
        "content": (
            "Singles offer more floor space but still have limited closet depth. "
            "A compact desk organizer and one extra seating option are usually "
            "enough before buying large furniture."
        ),
        "tags": ["packing", "room", "single", "storage", "checklist"],
        "risk_level": "low",
    },
    {
        "doc_id": "rule-microwave-fridge",
        "title": "Microwave and mini-fridge combos",
        "source_type": "generic_rule",
        "content": (
            "Combination microwave/fridge units may need housing approval and "
            "shared coordination. Wattage and size limits are school-specific "
            "and must be checked before purchase."
        ),
        "tags": ["rules", "appliances", "roommate", "prohibited"],
        "risk_level": "medium",
    },
    {
        "doc_id": "budget-textbooks-vs-dorm",
        "title": "Separate textbook and dorm budgets",
        "source_type": "budget_tip",
        "content": (
            "Course materials can rival dorm setup costs. Track textbook "
            "spending separately so move-in shopping does not crowd out "
            "required academic expenses."
        ),
        "tags": ["budget", "school", "priorities", "shopping"],
        "risk_level": "low",
    },
    {
        "doc_id": "logistics-car-packing",
        "title": "Driving vs flying tradeoffs",
        "source_type": "logistics_tip",
        "content": (
            "Driving allows bulky items in the car but still benefits from a "
            "packing list by room zone. Flying students should defer bulky "
            "purchases until after arrival."
        ),
        "tags": ["logistics", "transportation", "flight", "car", "packing"],
        "risk_level": "low",
    },
]
