"""
First Aid Knowledge Base for Arohan Health App
Wound Care & Minor Injury Management
50 structured records for RAG database ingestion
"""

FIRST_AID_DOCUMENTS = [

    # ─── HEAD WOUNDS ────────────────────────────────────────────────────────────

    {
        "id": "fa_head_001",
        "category": "head_wound",
        "wound_type": "minor_cut",
        "title": "Immediate Pressure for Head Cut",
        "content": (
            "For a minor cut on the head, immediately apply firm and steady pressure "
            "using a clean cloth or sterile gauze pad. Head wounds bleed more than cuts "
            "on other body parts because the scalp has many blood vessels. Press firmly "
            "for at least 10 to 15 minutes without lifting the cloth to check, as lifting "
            "can disturb the clot that is forming. If the cloth soaks through, add another "
            "layer on top without removing the first one."
        ),
        "severity_applicable": "minor",
        "tags": ["head", "cut", "pressure", "bleeding", "scalp"],
    },

    {
        "id": "fa_head_002",
        "category": "head_wound",
        "wound_type": "minor_cut",
        "title": "Cleaning a Head Wound",
        "content": (
            "Once bleeding has slowed or stopped, gently clean the head wound with clean "
            "running water for at least 5 minutes. Use a mild soap around the wound edges "
            "but do not let soap enter the wound itself. Remove any visible dirt or debris "
            "carefully using clean tweezers if needed. Do not scrub the wound directly, "
            "as this can cause more bleeding and tissue damage. Pat the area dry with a "
            "clean cloth after rinsing."
        ),
        "severity_applicable": "minor",
        "tags": ["head", "cleaning", "wound", "water", "debris"],
    },

    {
        "id": "fa_head_003",
        "category": "head_wound",
        "wound_type": "minor_cut",
        "title": "Antiseptic Application on Head Wound",
        "content": (
            "After cleaning, apply a thin layer of antiseptic solution such as povidone-iodine "
            "or chlorhexidine to the head wound to prevent infection. Avoid using hydrogen "
            "peroxide or alcohol directly on the wound as these can damage healthy tissue "
            "and slow the healing process. Antiseptic ointment like Neosporin or Betadine "
            "can also be applied to keep the wound moist and reduce infection risk. Reapply "
            "once daily or when changing the dressing."
        ),
        "severity_applicable": "minor",
        "tags": ["head", "antiseptic", "infection", "betadine", "ointment"],
    },

    {
        "id": "fa_head_004",
        "category": "head_wound",
        "wound_type": "minor_cut",
        "title": "Bandaging a Minor Head Cut",
        "content": (
            "Cover a minor head cut with a sterile adhesive bandage or gauze pad secured "
            "with medical tape. For cuts on the scalp hidden by hair, a simple gauze dressing "
            "held in place with a bandage wrap may work better than adhesive strips. Ensure "
            "the bandage is snug but not too tight, as excessive pressure on the head can "
            "be uncomfortable. Change the dressing every 24 hours or whenever it becomes "
            "wet or dirty to prevent bacterial growth."
        ),
        "severity_applicable": "minor",
        "tags": ["head", "bandage", "dressing", "gauze", "scalp"],
    },

    {
        "id": "fa_head_005",
        "category": "head_wound",
        "wound_type": "minor_cut",
        "title": "Using Butterfly Strips on Head Cuts",
        "content": (
            "For small but gaping cuts on the forehead or scalp that are minor in depth, "
            "butterfly closure strips or steri-strips can be used to hold the wound edges "
            "together. Clean and dry the area thoroughly before applying. Place the strips "
            "perpendicular to the wound, gently pulling the skin edges together. These strips "
            "help the wound heal with minimal scarring. Do not apply if the wound is actively "
            "bleeding. Leave strips in place for 5 to 7 days."
        ),
        "severity_applicable": "minor",
        "tags": ["head", "butterfly strip", "steri-strip", "wound closure", "forehead"],
    },

    # ─── GENERAL CUTS & LACERATIONS ─────────────────────────────────────────────

    {
        "id": "fa_cut_001",
        "category": "general_cut",
        "wound_type": "laceration",
        "title": "Stop Bleeding with Elevation",
        "content": (
            "To help control bleeding from a minor cut, elevate the injured area above "
            "the level of the heart whenever possible. For a hand or arm cut, raise the "
            "limb up. For a leg cut, lie down and prop the leg on a pillow or rolled cloth. "
            "Elevation reduces blood pressure at the wound site, slowing blood flow and "
            "helping the clot form faster. Combine elevation with direct pressure for best "
            "results in stopping minor bleeding."
        ),
        "severity_applicable": "minor",
        "tags": ["bleeding", "elevation", "cut", "laceration", "clot"],
    },

    {
        "id": "fa_cut_002",
        "category": "general_cut",
        "wound_type": "laceration",
        "title": "Identifying Minor vs Major Wound",
        "content": (
            "A wound is classified as minor if it is less than 2 centimetres in length, "
            "the bleeding stops within 10 to 15 minutes of applying pressure, the wound "
            "edges can be brought together easily, and there is no visible fat, muscle, or "
            "bone. Minor wounds do not cause numbness, severe pain out of proportion to "
            "the injury, or loss of movement. If any of these signs are present, the wound "
            "may be major and requires immediate medical attention."
        ),
        "severity_applicable": "minor",
        "tags": ["classification", "minor", "major", "wound", "assessment"],
    },

    {
        "id": "fa_cut_003",
        "category": "general_cut",
        "wound_type": "laceration",
        "title": "Proper Hand Washing Before Wound Care",
        "content": (
            "Before treating any wound, thoroughly wash your hands with soap and water "
            "for at least 20 seconds to prevent introducing bacteria into the wound. If "
            "soap and water are not available, use an alcohol-based hand sanitizer with "
            "at least 60 percent alcohol content. Avoid touching the wound directly with "
            "unwashed hands. If available, wear disposable gloves before handling the "
            "wound or dressing to maintain sterile conditions during first aid."
        ),
        "severity_applicable": "minor",
        "tags": ["hygiene", "hand wash", "sterile", "bacteria", "gloves"],
    },

    {
        "id": "fa_cut_004",
        "category": "general_cut",
        "wound_type": "laceration",
        "title": "Wound Irrigation Technique",
        "content": (
            "Irrigating the wound with clean water or saline solution is the most effective "
            "way to remove bacteria and debris. Use a syringe or clean squeeze bottle to "
            "gently flush the wound with a steady stream of water. Irrigation pressure "
            "should be enough to dislodge dirt but not so forceful that it damages tissue. "
            "Irrigate for at least 5 to 10 minutes. Tap water that is safe to drink is "
            "acceptable for wound irrigation and is often just as effective as sterile saline."
        ),
        "severity_applicable": "minor",
        "tags": ["irrigation", "saline", "water", "cleaning", "debris"],
    },

    {
        "id": "fa_cut_005",
        "category": "general_cut",
        "wound_type": "laceration",
        "title": "Recognising Signs of Wound Infection",
        "content": (
            "After initial first aid, monitor the wound daily for signs of infection. "
            "Warning signs include increasing redness spreading around the wound, warmth "
            "or swelling that worsens after 24 hours, yellow or green pus discharge, "
            "an unpleasant smell from the wound, fever above 38 degrees Celsius, and "
            "red streaks spreading from the wound toward the body. If any of these signs "
            "appear, stop home treatment and consult a doctor immediately, as the wound "
            "may need antibiotics or professional cleaning."
        ),
        "severity_applicable": "minor",
        "tags": ["infection", "pus", "redness", "fever", "monitoring"],
    },

    # ─── ABRASIONS & SCRAPES ─────────────────────────────────────────────────────

    {
        "id": "fa_abr_001",
        "category": "abrasion",
        "wound_type": "scrape",
        "title": "First Aid for Skin Scrapes and Abrasions",
        "content": (
            "A scrape or abrasion is when the outer layers of skin are rubbed away. "
            "First, rinse the scraped area under cool running water for 5 minutes to "
            "remove all dirt and grit. Gently use a soft clean cloth or gauze to wipe "
            "away remaining debris. Apply an antiseptic cream, then cover with a non-stick "
            "dressing or bandage. Change the dressing daily. Abrasions heal from the edges "
            "inward and usually heal within 5 to 10 days if kept clean and moist."
        ),
        "severity_applicable": "minor",
        "tags": ["abrasion", "scrape", "skin", "cleaning", "dressing"],
    },

    {
        "id": "fa_abr_002",
        "category": "abrasion",
        "wound_type": "scrape",
        "title": "Keeping Abrasions Moist for Faster Healing",
        "content": (
            "Moist wound healing significantly speeds up recovery from abrasions compared "
            "to letting wounds dry out and form scabs. Apply a thin layer of petroleum jelly "
            "or an antibiotic ointment to keep the wound surface moist. Cover with a "
            "non-stick sterile pad. A moist environment prevents the wound from drying into "
            "a hard scab that can crack and bleed, reduces pain, and promotes new skin cell "
            "migration across the wound. Change the dressing and reapply ointment daily."
        ),
        "severity_applicable": "minor",
        "tags": ["abrasion", "moist", "petroleum jelly", "healing", "scab"],
    },

    {
        "id": "fa_abr_003",
        "category": "abrasion",
        "wound_type": "scrape",
        "title": "Removing Embedded Grit from Abrasions",
        "content": (
            "Embedded dirt or gravel in an abrasion must be removed to prevent tattooing, "
            "which is permanent skin discolouration from trapped particles. After soaking "
            "the area with clean water, use clean tweezers or a soft-bristled clean "
            "toothbrush to gently scrub out particles. This may be uncomfortable but is "
            "essential. If particles remain deeply embedded after thorough cleaning, do "
            "not force removal — seek medical attention for professional debridement instead "
            "of risking further skin damage."
        ),
        "severity_applicable": "minor",
        "tags": ["abrasion", "grit", "debris", "tweezers", "tattooing"],
    },

    # ─── BLEEDING CONTROL ────────────────────────────────────────────────────────

    {
        "id": "fa_bleed_001",
        "category": "bleeding_control",
        "wound_type": "general",
        "title": "Direct Pressure Technique for Wound Bleeding",
        "content": (
            "Direct pressure is the most effective first aid technique to control bleeding "
            "from minor wounds. Place a clean folded cloth or sterile gauze directly over "
            "the wound and press firmly using the palm of your hand. Maintain continuous "
            "pressure for a minimum of 10 to 15 minutes. Resist the urge to peek, as "
            "releasing pressure prematurely can disrupt clot formation. If blood soaks "
            "through, place additional cloth on top and continue pressing. Only release "
            "pressure once bleeding has clearly stopped."
        ),
        "severity_applicable": "minor",
        "tags": ["bleeding", "pressure", "gauze", "clot", "control"],
    },

    {
        "id": "fa_bleed_002",
        "category": "bleeding_control",
        "wound_type": "general",
        "title": "Cold Compress to Reduce Bleeding and Swelling",
        "content": (
            "Applying a cold compress or ice pack wrapped in a cloth to the area around "
            "a minor wound can help reduce bleeding and swelling. Cold causes blood vessels "
            "to constrict, which slows blood flow to the area. Apply for 10 minutes on, "
            "then 10 minutes off. Never place ice directly on skin or on an open wound, "
            "as this can cause frostbite and tissue damage. Cold therapy is most helpful "
            "in the first hour after injury, especially for wounds with surrounding bruising "
            "or swelling."
        ),
        "severity_applicable": "minor",
        "tags": ["bleeding", "cold", "ice", "swelling", "compress"],
    },

    {
        "id": "fa_bleed_003",
        "category": "bleeding_control",
        "wound_type": "general",
        "title": "When to Seek Emergency Help for Bleeding",
        "content": (
            "Seek emergency medical help immediately if bleeding does not stop after "
            "15 to 20 minutes of continuous direct pressure, if the wound is spurting "
            "bright red blood (indicating artery damage), if the person becomes pale, "
            "dizzy, confused, or loses consciousness, if blood loss appears to be greater "
            "than half a cup, or if the wound is located on the neck, chest, or abdomen. "
            "These are signs of major bleeding that is beyond the scope of home first aid "
            "and requires urgent professional care."
        ),
        "severity_applicable": "major",
        "tags": ["bleeding", "emergency", "artery", "seek help", "danger signs"],
    },

    # ─── WOUND DRESSING & BANDAGING ─────────────────────────────────────────────

    {
        "id": "fa_dress_001",
        "category": "dressing",
        "wound_type": "general",
        "title": "Choosing the Right Dressing for a Minor Wound",
        "content": (
            "The right dressing protects the wound from infection and supports healing. "
            "For small cuts, use adhesive bandage strips. For larger minor wounds, use a "
            "sterile non-adherent pad secured with medical tape. For wounds that are "
            "oozing, an absorbent gauze pad is appropriate. Hydrocolloid dressings are "
            "excellent for abrasions and blisters as they maintain moisture. Avoid using "
            "fluffy cotton wool directly on wounds as the fibres can stick to the wound "
            "surface and cause pain and damage when removed."
        ),
        "severity_applicable": "minor",
        "tags": ["dressing", "bandage", "hydrocolloid", "gauze", "adhesive"],
    },

    {
        "id": "fa_dress_002",
        "category": "dressing",
        "wound_type": "general",
        "title": "How Often to Change a Wound Dressing",
        "content": (
            "Change the wound dressing once daily under normal circumstances. Change it "
            "immediately if the dressing becomes wet, dirty, or soaked through with blood "
            "or discharge. When removing the old dressing, do so gently and slowly to "
            "avoid disturbing the healing tissue. If the dressing sticks to the wound, "
            "soak it briefly with clean water or saline to loosen it before pulling. "
            "After removing the dressing, inspect the wound for signs of infection before "
            "cleaning and applying a fresh dressing."
        ),
        "severity_applicable": "minor",
        "tags": ["dressing", "change", "frequency", "daily", "inspection"],
    },

    {
        "id": "fa_dress_003",
        "category": "dressing",
        "wound_type": "general",
        "title": "Securing a Dressing Without Cutting Off Circulation",
        "content": (
            "When applying bandage tape or a wrap to secure a dressing, make sure it is "
            "firm enough to stay in place but not so tight that it cuts off circulation. "
            "Signs that a bandage is too tight include numbness or tingling below the "
            "dressing, skin turning pale, blue, or very cold below the bandage, and "
            "increasing pain or throbbing. If any of these occur, immediately loosen "
            "or remove the bandage and reapply with less tension. On limbs, you should "
            "always be able to slip a finger under the bandage easily."
        ),
        "severity_applicable": "minor",
        "tags": ["bandage", "circulation", "tight", "numbness", "dressing"],
    },

    # ─── INFECTION PREVENTION ────────────────────────────────────────────────────

    {
        "id": "fa_infect_001",
        "category": "infection_prevention",
        "wound_type": "general",
        "title": "Tetanus Risk and Wound First Aid",
        "content": (
            "Tetanus is a serious bacterial infection that can enter through even minor "
            "wounds, especially those caused by dirty or rusty objects, animal scratches, "
            "or deep puncture wounds. If the wounded person has not had a tetanus booster "
            "in the past 5 years, they should see a doctor for a booster dose after first "
            "aid. Clean the wound thoroughly regardless of tetanus vaccination status. "
            "Symptoms of tetanus include jaw stiffness, muscle spasms, and difficulty "
            "swallowing and can appear 3 to 21 days after injury."
        ),
        "severity_applicable": "minor",
        "tags": ["tetanus", "infection", "vaccination", "booster", "prevention"],
    },

    {
        "id": "fa_infect_002",
        "category": "infection_prevention",
        "wound_type": "general",
        "title": "Antibiotic Ointment for Wound Care",
        "content": (
            "Applying a thin layer of over-the-counter antibiotic ointment such as "
            "Neosporin or Bacitracin to a clean minor wound helps prevent bacterial "
            "infection and keeps the wound moist for better healing. Use only a small "
            "amount and apply once daily with each dressing change. Stop using if you "
            "notice any allergic reaction such as a rash, increased redness, or itching "
            "around the wound, as some people are sensitive to neomycin found in some "
            "antibiotic ointments. Consult a pharmacist if unsure which product to use."
        ),
        "severity_applicable": "minor",
        "tags": ["antibiotic", "ointment", "neosporin", "infection", "prevention"],
    },

    {
        "id": "fa_infect_003",
        "category": "infection_prevention",
        "wound_type": "general",
        "title": "Keeping Wounds Dry vs Moist: What is Correct",
        "content": (
            "The old advice of letting wounds air dry and form scabs is outdated. Modern "
            "wound care research shows that wounds covered with a moist dressing and "
            "antibiotic ointment heal up to 50 percent faster than wounds left to dry out. "
            "However, moist does not mean wet or waterlogged. Keep the wound surface gently "
            "moistened under a clean dressing. Avoid soaking the wound in water for long "
            "periods, swimming, or exposing it to dirt. Shower briefly and pat dry, then "
            "reapply dressing promptly."
        ),
        "severity_applicable": "minor",
        "tags": ["moist", "healing", "dressing", "wound care", "scab"],
    },

    # ─── SWELLING & BRUISING ─────────────────────────────────────────────────────

    {
        "id": "fa_swel_001",
        "category": "swelling_bruising",
        "wound_type": "bruise",
        "title": "RICE Method for Minor Injuries with Swelling",
        "content": (
            "The RICE method stands for Rest, Ice, Compression, and Elevation and is "
            "the standard first aid approach for minor injuries involving swelling and "
            "bruising. Rest the injured area. Apply ice wrapped in cloth for 20 minutes "
            "every 2 hours. Use a compression bandage to reduce swelling. Elevate the "
            "area above heart level. Begin RICE within the first hour of injury for "
            "best results. Continue RICE for the first 24 to 48 hours. Avoid heat, "
            "alcohol, and massage in the first 24 hours as they can worsen swelling."
        ),
        "severity_applicable": "minor",
        "tags": ["RICE", "swelling", "bruise", "compression", "elevation"],
    },

    {
        "id": "fa_swel_002",
        "category": "swelling_bruising",
        "wound_type": "bruise",
        "title": "Treating a Bruise Around a Wound",
        "content": (
            "Bruising around a minor wound is normal and indicates internal bleeding in "
            "the tissue. Apply a cold pack wrapped in cloth to the bruised area for "
            "10 to 15 minutes to reduce discolouration and pain. Do not apply the cold "
            "pack directly over an open wound. The bruise will change colour over days "
            "from dark purple to green to yellow as the body reabsorbs the blood. This "
            "colour progression is normal. If a bruise grows rapidly, feels hard, or "
            "the swelling increases significantly, seek medical evaluation."
        ),
        "severity_applicable": "minor",
        "tags": ["bruise", "swelling", "cold pack", "discolouration", "wound"],
    },

    # ─── PAIN MANAGEMENT ─────────────────────────────────────────────────────────

    {
        "id": "fa_pain_001",
        "category": "pain_management",
        "wound_type": "general",
        "title": "Over-the-Counter Pain Relief for Minor Wounds",
        "content": (
            "For pain associated with minor wounds, over-the-counter pain relievers can "
            "help. Paracetamol (acetaminophen) is the safest option for most people and "
            "effectively reduces wound pain without affecting bleeding. Ibuprofen can "
            "also reduce pain and inflammation but should be avoided in the first 24 hours "
            "as it can increase bleeding tendency. Follow package dosage instructions and "
            "do not exceed recommended doses. Avoid aspirin for wound pain in children "
            "and teenagers as it carries a risk of Reye's syndrome."
        ),
        "severity_applicable": "minor",
        "tags": ["pain", "paracetamol", "ibuprofen", "relief", "medication"],
    },

    {
        "id": "fa_pain_002",
        "category": "pain_management",
        "wound_type": "general",
        "title": "Distraction Techniques for Wound Pain in Children",
        "content": (
            "For children experiencing pain during wound first aid, distraction techniques "
            "can significantly reduce perceived pain and anxiety. Engage the child with "
            "conversation, a favourite toy, or a video during wound cleaning. Having the "
            "child take slow deep breaths or blow bubbles can reduce pain sensation. "
            "Praise cooperation and explain each step in simple, calm language before "
            "doing it. Avoid using scary words and reassure the child throughout. "
            "Cold numbing spray applied briefly before cleaning can also reduce discomfort."
        ),
        "severity_applicable": "minor",
        "tags": ["pain", "children", "distraction", "anxiety", "pediatric"],
    },

    # ─── SPECIFIC BODY PART WOUNDS ───────────────────────────────────────────────

    {
        "id": "fa_part_001",
        "category": "body_part_specific",
        "wound_type": "finger_cut",
        "title": "First Aid for a Cut Finger",
        "content": (
            "For a minor cut on the finger, elevate the hand above heart level and apply "
            "firm pressure with a clean cloth for 10 to 15 minutes. Once bleeding stops, "
            "rinse under cool water and apply antiseptic. Use an adhesive bandage to cover "
            "the wound. Make sure the bandage is not wrapped too tightly around the finger "
            "as this can restrict blood flow. If the cut is across a joint or you notice "
            "difficulty bending the finger, there may be tendon involvement and you should "
            "seek medical attention. Change the finger bandage daily and keep it dry."
        ),
        "severity_applicable": "minor",
        "tags": ["finger", "cut", "hand", "bandage", "tendon"],
    },

    {
        "id": "fa_part_002",
        "category": "body_part_specific",
        "wound_type": "knee_scrape",
        "title": "First Aid for Scraped Knee",
        "content": (
            "A scraped knee is one of the most common minor wounds, especially in children. "
            "First, rinse the knee under cool running water for 5 minutes to flush out "
            "dirt. Gently remove remaining debris with clean tweezers. Apply antiseptic "
            "cream and cover with a large sterile non-stick pad secured with medical tape "
            "or a self-adhesive dressing designed for knees. Since the knee bends, use a "
            "dressing that can flex and stretch without peeling off. Keep the wound covered "
            "for physical activity and check daily for signs of infection."
        ),
        "severity_applicable": "minor",
        "tags": ["knee", "scrape", "child", "dressing", "abrasion"],
    },

    {
        "id": "fa_part_003",
        "category": "body_part_specific",
        "wound_type": "palm_cut",
        "title": "First Aid for a Cut on the Palm",
        "content": (
            "Cuts on the palm bleed heavily because the palm has a rich blood supply. "
            "Apply firm pressure immediately using a folded cloth and elevate the hand. "
            "For palm cuts, making a fist around the dressing and applying external "
            "pressure can help control bleeding. Once bleeding stops, clean gently "
            "and apply antiseptic. A deep palm cut may involve nerves or tendons "
            "supplying the fingers. If you notice numbness, tingling, or difficulty "
            "moving fingers normally, seek medical attention even if the wound appears "
            "minor on the surface."
        ),
        "severity_applicable": "minor",
        "tags": ["palm", "hand", "cut", "bleeding", "nerves"],
    },

    {
        "id": "fa_part_004",
        "category": "body_part_specific",
        "wound_type": "forehead_cut",
        "title": "First Aid for a Forehead Cut",
        "content": (
            "Forehead cuts bleed profusely due to the rich scalp blood supply but are "
            "often more superficial than they appear. Apply steady pressure with a clean "
            "cloth for 15 minutes. Once bleeding is controlled, clean the area and "
            "apply butterfly strips or steri-strips to close a gaping wound. These "
            "are preferred over regular bandages for forehead cuts as they hold the "
            "skin edges together and reduce scarring. Check for signs of concussion "
            "such as confusion, dizziness, or nausea if the cut was caused by a blow "
            "to the head, and seek emergency care if these appear."
        ),
        "severity_applicable": "minor",
        "tags": ["forehead", "cut", "scalp", "concussion", "steri-strip"],
    },

    {
        "id": "fa_part_005",
        "category": "body_part_specific",
        "wound_type": "foot_wound",
        "title": "First Aid for Minor Foot Wounds",
        "content": (
            "Foot wounds require extra attention because feet are exposed to more bacteria "
            "and harder to keep clean. Wash the foot wound thoroughly and apply antiseptic. "
            "Keep the foot elevated when resting to reduce swelling. Use a waterproof "
            "dressing or cover the dressing with a waterproof boot cover when showering. "
            "Avoid walking barefoot while the wound heals to prevent contamination and "
            "re-injury. For people with diabetes, any foot wound — no matter how minor "
            "it appears — should be evaluated by a healthcare professional promptly due "
            "to the elevated risk of infection and complications."
        ),
        "severity_applicable": "minor",
        "tags": ["foot", "wound", "diabetes", "waterproof", "bacteria"],
    },

    # ─── SPECIAL WOUND TYPES ─────────────────────────────────────────────────────

    {
        "id": "fa_spec_001",
        "category": "special_wounds",
        "wound_type": "blister",
        "title": "First Aid for Blisters",
        "content": (
            "A blister is the body's natural protection for the skin beneath it. Do not "
            "pop a blister unless it is very large, extremely painful, or in a location "
            "that will inevitably burst. If you must drain it, clean a needle with alcohol, "
            "pierce the edge of the blister, and let the fluid drain while keeping the "
            "overlying skin intact. Apply antibiotic ointment and cover with a sterile "
            "pad. If the blister roof tears off on its own, treat the raw skin underneath "
            "as an open wound. Hydrocolloid dressings are ideal for blisters as they "
            "protect the area and promote healing."
        ),
        "severity_applicable": "minor",
        "tags": ["blister", "friction", "drain", "hydrocolloid", "skin"],
    },

    {
        "id": "fa_spec_002",
        "category": "special_wounds",
        "wound_type": "puncture",
        "title": "First Aid for Minor Puncture Wounds",
        "content": (
            "Minor puncture wounds from nails, thorns, or small sharp objects require "
            "careful first aid. Do not probe the wound or try to widen it. Allow the "
            "wound to bleed slightly to help flush out bacteria. Rinse under running "
            "water for 10 minutes. Apply antiseptic and cover with a small bandage. "
            "Puncture wounds carry a higher risk of deep infection including tetanus "
            "because they are narrow and difficult to clean. Monitor closely for infection "
            "signs over the next 2 to 3 days. Seek medical advice if the puncturing "
            "object was dirty, rusty, or if the wound is on the foot."
        ),
        "severity_applicable": "minor",
        "tags": ["puncture", "nail", "tetanus", "deep", "infection"],
    },

    {
        "id": "fa_spec_003",
        "category": "special_wounds",
        "wound_type": "animal_scratch",
        "title": "First Aid for Minor Animal Scratches",
        "content": (
            "Minor scratches from cats, dogs, or other animals can carry bacteria in "
            "their claws. Wash the scratch thoroughly under running water with soap for "
            "at least 5 minutes. Apply antiseptic and cover with a bandage. Monitor the "
            "scratch closely for redness, swelling, or pus. Cat scratches can cause Cat "
            "Scratch Disease, a bacterial infection causing swollen lymph nodes. Dog and "
            "cat scratches rarely cause rabies, but if an animal's vaccination status is "
            "unknown or the animal behaved strangely, consult a doctor about rabies "
            "post-exposure prophylaxis as a precaution."
        ),
        "severity_applicable": "minor",
        "tags": ["animal", "scratch", "cat", "dog", "rabies", "bacteria"],
    },

    {
        "id": "fa_spec_004",
        "category": "special_wounds",
        "wound_type": "splinter",
        "title": "Removing a Splinter Safely",
        "content": (
            "To remove a splinter, clean the affected area and a pair of fine-tipped "
            "tweezers with antiseptic. Grasp the splinter as close to the skin surface "
            "as possible and pull it out in the same direction it entered. After removal, "
            "clean the area, apply antiseptic, and cover with a bandage. If the splinter "
            "is deeply embedded, not fully visible, or breaking apart during removal, "
            "stop and seek medical help. A retained splinter can cause infection and "
            "foreign body reaction. Watch for signs of infection at the site over "
            "the following days."
        ),
        "severity_applicable": "minor",
        "tags": ["splinter", "tweezers", "foreign body", "removal", "infection"],
    },

    {
        "id": "fa_spec_005",
        "category": "special_wounds",
        "wound_type": "burn_minor",
        "title": "First Aid for Minor Burns (First Degree)",
        "content": (
            "For minor first-degree burns affecting only the outer skin layer, run cool "
            "water over the burn for 10 to 20 minutes immediately. Do not use ice, ice "
            "water, toothpaste, butter, or any home remedies as these cause further skin "
            "damage. After cooling, apply a gentle moisturising lotion or aloe vera gel "
            "to soothe the skin. Cover loosely with a sterile non-stick bandage. Take "
            "paracetamol or ibuprofen for pain. Minor burns usually heal within 3 to "
            "5 days. Seek medical attention if the burn is larger than 3 centimetres, "
            "involves the face, hands, or joints, or if blisters form."
        ),
        "severity_applicable": "minor",
        "tags": ["burn", "first degree", "cool water", "aloe vera", "skin"],
    },

    # ─── HEALING NUTRITION & LIFESTYLE ──────────────────────────────────────────

    {
        "id": "fa_heal_001",
        "category": "healing_support",
        "wound_type": "general",
        "title": "Nutrition to Speed Up Wound Healing",
        "content": (
            "Proper nutrition plays a critical role in wound healing. Vitamin C is essential "
            "for collagen synthesis — eat citrus fruits, guava, bell peppers, and amla. "
            "Protein is needed to rebuild tissue — include eggs, lentils, chicken, and "
            "paneer in meals. Zinc supports immune function and cell growth — found in "
            "pumpkin seeds, chickpeas, and meat. Vitamin A promotes skin repair — found in "
            "carrots, sweet potato, and spinach. Stay well hydrated with at least 2 to "
            "3 litres of water daily. Avoid alcohol and smoking as these significantly "
            "slow the healing process."
        ),
        "severity_applicable": "minor",
        "tags": ["nutrition", "vitamin C", "protein", "zinc", "healing", "diet"],
    },

    {
        "id": "fa_heal_002",
        "category": "healing_support",
        "wound_type": "general",
        "title": "Rest and Sleep for Wound Recovery",
        "content": (
            "The body repairs tissue most actively during sleep, when growth hormone "
            "levels peak and cell regeneration accelerates. Getting 7 to 9 hours of "
            "quality sleep each night significantly speeds wound healing. Avoid activities "
            "that strain or stress the wound site. Keep the wounded area protected from "
            "physical pressure during sleep. For head and face wounds, sleeping slightly "
            "propped up can reduce swelling overnight. Avoid vigorous physical activity "
            "for at least 2 to 3 days after a minor wound to prevent reopening the wound "
            "or increasing bleeding."
        ),
        "severity_applicable": "minor",
        "tags": ["sleep", "rest", "recovery", "growth hormone", "healing"],
    },

    {
        "id": "fa_heal_003",
        "category": "healing_support",
        "wound_type": "general",
        "title": "Sun Protection During Wound Healing",
        "content": (
            "New skin formed during wound healing is extremely sensitive to ultraviolet "
            "radiation from the sun. UV exposure on a healing wound or fresh scar can "
            "cause permanent hyperpigmentation and worsened scarring. Keep the healing "
            "wound covered and protected from direct sunlight. Once the wound has closed "
            "and the dressing is no longer needed, apply sunscreen with SPF 30 or higher "
            "over the healing scar. Continue sun protection for at least 6 months after "
            "the wound has healed to prevent long-term scar discolouration."
        ),
        "severity_applicable": "minor",
        "tags": ["sun", "UV", "scar", "sunscreen", "pigmentation", "healing"],
    },

    {
        "id": "fa_heal_004",
        "category": "healing_support",
        "wound_type": "general",
        "title": "Scar Prevention and Management",
        "content": (
            "To minimise scarring from a minor wound, keep the wound closed and moist "
            "during healing using steri-strips and antibiotic ointment. Once the wound "
            "has fully closed, applying silicone gel sheets or silicone gel over the "
            "scar for several weeks has strong evidence for reducing scar thickness and "
            "redness. Gentle scar massage with a moisturiser for 5 minutes twice daily "
            "after the wound is fully closed helps soften the scar. Avoid picking at "
            "scabs as this disrupts healing and increases scarring risk significantly."
        ),
        "severity_applicable": "minor",
        "tags": ["scar", "silicone", "prevention", "massage", "healing"],
    },

    # ─── WOUND MONITORING & FOLLOW UP ───────────────────────────────────────────

    {
        "id": "fa_mon_001",
        "category": "monitoring",
        "wound_type": "general",
        "title": "Daily Wound Inspection Checklist",
        "content": (
            "Perform a daily inspection of your wound when changing the dressing. "
            "Check for: reduced swelling and redness compared to the day before (good); "
            "the wound edges appearing to come together (good sign of healing); "
            "clear or light yellow fluid seeping from the wound which is normal plasma; "
            "a thin pink line forming at the wound edges indicating new skin growth. "
            "Concerning signs that require medical consultation include: pus (thick yellow "
            "or green discharge), increasing pain or redness spreading outward, foul odour, "
            "wound edges separating, or fever. Document changes if possible."
        ),
        "severity_applicable": "minor",
        "tags": ["monitoring", "inspection", "daily", "healing", "signs"],
    },

    {
        "id": "fa_mon_002",
        "category": "monitoring",
        "wound_type": "general",
        "title": "Expected Healing Timeline for Minor Wounds",
        "content": (
            "Understanding the typical healing stages helps in knowing whether a wound is "
            "healing normally. Days 1 to 3: Bleeding stops, wound swells and becomes red "
            "as immune cells arrive — this is the inflammatory phase and is normal. "
            "Days 4 to 7: Wound edges begin to close, new pink skin forms at the edges, "
            "and swelling reduces. Days 7 to 14: A thin pink scar line forms as the wound "
            "fully closes. If bleeding restarts, swelling increases, or the wound does not "
            "show closing progress by day 7, seek medical evaluation as the wound may "
            "need additional treatment."
        ),
        "severity_applicable": "minor",
        "tags": ["healing", "timeline", "stages", "days", "progress"],
    },

    {
        "id": "fa_mon_003",
        "category": "monitoring",
        "wound_type": "general",
        "title": "When a Minor Wound Needs Stitches",
        "content": (
            "A minor wound may still require stitches or medical closure if it is gaping "
            "and the edges cannot be held together naturally, if it is longer than 2 "
            "centimetres, located on the face where scarring is visible, or if it has "
            "jagged uneven edges. Stitches are most effective if applied within 6 to 8 "
            "hours of the injury. After 12 hours, most doctors prefer to leave the wound "
            "open to avoid trapping infection inside. If you think stitches may be needed, "
            "control the bleeding, keep the wound clean and covered, and go to a clinic "
            "or emergency department promptly."
        ),
        "severity_applicable": "minor",
        "tags": ["stitches", "sutures", "closure", "gaping", "scar"],
    },

    # ─── FIRST AID KIT & PREPAREDNESS ───────────────────────────────────────────

    {
        "id": "fa_kit_001",
        "category": "preparedness",
        "wound_type": "general",
        "title": "Essential Items in a Home First Aid Kit for Wounds",
        "content": (
            "Every home should have a first aid kit stocked with wound care essentials. "
            "These include: sterile gauze pads in multiple sizes, adhesive bandage strips "
            "in various sizes, medical tape, antiseptic solution such as povidone-iodine, "
            "antibiotic ointment, sterile saline solution for wound irrigation, clean "
            "disposable gloves, fine-tipped tweezers, scissors, butterfly closure strips, "
            "a digital thermometer, and paracetamol or ibuprofen tablets. Store the kit "
            "in a cool dry place, check expiry dates every 6 months, and restock used "
            "items promptly."
        ),
        "severity_applicable": "minor",
        "tags": ["first aid kit", "preparation", "supplies", "gauze", "antiseptic"],
    },

    {
        "id": "fa_kit_002",
        "category": "preparedness",
        "wound_type": "general",
        "title": "Saline Solution Preparation at Home",
        "content": (
            "If sterile saline is not available, you can prepare a safe substitute at "
            "home for wound irrigation. Boil 1 litre of water and let it cool completely. "
            "Add 9 grams or approximately one and a half teaspoons of table salt and "
            "stir until fully dissolved. This creates a 0.9 percent saline solution that "
            "closely matches the body's natural fluid concentration and is safe for wound "
            "cleaning. Use within 24 hours and store in a clean sealed container. Discard "
            "any unused solution after 24 hours and make a fresh batch if needed."
        ),
        "severity_applicable": "minor",
        "tags": ["saline", "homemade", "wound irrigation", "preparation", "salt water"],
    },

    # ─── CHILDREN & ELDERLY SPECIFIC ────────────────────────────────────────────

    {
        "id": "fa_eld_001",
        "category": "special_populations",
        "wound_type": "general",
        "title": "Wound Care Considerations for Elderly Patients",
        "content": (
            "Elderly skin is thinner, more fragile, and heals more slowly than younger "
            "skin. Use low-adhesion dressings and tape to avoid further skin damage on "
            "removal. Avoid strong antiseptics like hydrogen peroxide on elderly skin as "
            "they can cause additional tissue damage. Inspect wounds daily as signs of "
            "infection may be less pronounced in older adults with a weakened immune "
            "response. Elderly patients with diabetes, heart conditions, or those on blood "
            "thinners such as warfarin will bleed longer and heal slower — seek medical "
            "review sooner rather than later for any wound in this group."
        ),
        "severity_applicable": "minor",
        "tags": ["elderly", "fragile skin", "blood thinner", "diabetes", "healing"],
    },

    {
        "id": "fa_eld_002",
        "category": "special_populations",
        "wound_type": "general",
        "title": "Safe Wound Care for Young Children",
        "content": (
            "Children are more prone to contaminating their wounds by touching them with "
            "dirty hands. Keep nails trimmed and hands clean. Use child-friendly dressings "
            "with colourful designs to encourage the child to leave the bandage alone. "
            "Explain the care process in simple language to reduce fear. Use child-safe "
            "antiseptics and avoid stinging solutions on children's wounds. Monitor wounds "
            "on children more frequently as children may not report increasing pain. "
            "For infants and toddlers, any wound should be evaluated by a doctor given "
            "the higher risk of rapid infection in young immune systems."
        ),
        "severity_applicable": "minor",
        "tags": ["children", "toddler", "infection", "bandage", "wound care"],
    },

    # ─── CULTURAL & INDIA-SPECIFIC FIRST AID ────────────────────────────────────

    {
        "id": "fa_ind_001",
        "category": "india_specific",
        "wound_type": "general",
        "title": "Common Harmful Home Remedies to Avoid",
        "content": (
            "Several traditional home remedies used in India can actually harm wounds and "
            "increase infection risk. Applying turmeric powder directly to an open wound "
            "can introduce contamination and delay healing despite its antibacterial "
            "properties in laboratory settings. Applying chilli, ghee, mustard oil, "
            "toothpaste, cow dung, or tobacco to a wound are harmful and should be "
            "strictly avoided. These substances can introduce infection, damage tissue, "
            "and make professional wound assessment harder. Clean the wound with clean "
            "water and use proper antiseptic and sterile dressings instead."
        ),
        "severity_applicable": "minor",
        "tags": ["home remedy", "turmeric", "avoid", "India", "traditional", "harmful"],
    },

    {
        "id": "fa_ind_002",
        "category": "india_specific",
        "wound_type": "general",
        "title": "Neem and Aloe Vera in Wound Care: What is Safe",
        "content": (
            "Neem leaves have documented antibacterial properties and neem-based creams "
            "available at pharmacies can be used around (not inside) a wound to prevent "
            "bacterial growth on surrounding skin. Aloe vera gel from the plant is safe "
            "and effective for soothing minor burns, abrasions, and skin irritation around "
            "wounds and can promote healing. However, raw plant material should not be "
            "placed directly into an open wound. Use commercially prepared, sterile "
            "formulations of these ingredients for wound care rather than applying raw "
            "plant material to avoid contamination."
        ),
        "severity_applicable": "minor",
        "tags": ["neem", "aloe vera", "natural", "India", "antibacterial", "safe"],
    },

    {
        "id": "fa_ind_003",
        "category": "india_specific",
        "wound_type": "general",
        "title": "Access to First Aid in Rural Settings",
        "content": (
            "In rural areas with limited access to pharmacies or medical facilities, "
            "certain safe alternatives can be used. Boiled and cooled water is a safe "
            "wound irrigant. Clean cotton cloth boiled and dried can serve as a sterile "
            "dressing in emergencies. Seek the nearest Primary Health Centre or Aarogya "
            "Kendra for wound evaluation if signs of infection develop. ASHA workers "
            "in villages are trained in basic first aid and can assist with wound "
            "management guidance. Do not delay seeking care for wounds that involve "
            "deep tissue, persistent bleeding, or signs of infection even in remote settings."
        ),
        "severity_applicable": "minor",
        "tags": ["rural", "India", "PHC", "ASHA", "access", "alternative"],
    },

    # ─── EMOTIONAL & PSYCHOLOGICAL SUPPORT ──────────────────────────────────────

    {
        "id": "fa_psych_001",
        "category": "psychological_support",
        "wound_type": "general",
        "title": "Calming a Person in Shock After a Wound",
        "content": (
            "After a minor wound, the person may experience shock-like symptoms such as "
            "pale skin, shaking, dizziness, nausea, or feeling faint — especially if they "
            "are frightened by the sight of blood. Help them sit or lie down safely and "
            "elevate their legs slightly if they feel faint. Speak in a calm, reassuring "
            "voice and explain what you are doing at each step. Loosen tight clothing "
            "around the neck and chest. Offer sips of water once they are feeling steadier "
            "and not nauseous. Do not leave the person alone until they are calm and stable. "
            "Emotional reassurance is as important as physical first aid."
        ),
        "severity_applicable": "minor",
        "tags": ["shock", "faint", "calm", "reassurance", "psychological", "blood"],
    },

    # ─── WOUND CLOSURE TECHNIQUES ───────────────────────────────────────────────

    {
        "id": "fa_close_001",
        "category": "wound_closure",
        "wound_type": "general",
        "title": "Using Adhesive Bandage Strips Correctly",
        "content": (
            "Adhesive bandage strips or plasters are suitable for clean, straight minor "
            "cuts under 2 centimetres. Ensure the wound and surrounding skin are clean "
            "and completely dry before applying, as bandages do not adhere to wet skin. "
            "Remove the backing without touching the pad. Place the pad over the wound "
            "and press the adhesive sides firmly onto the skin, pulling the wound edges "
            "together gently. Change the bandage daily and whenever it becomes wet or "
            "loose. Remove by pressing down on the skin while peeling the bandage back "
            "slowly to avoid skin damage."
        ),
        "severity_applicable": "minor",
        "tags": ["bandage", "plaster", "adhesive", "application", "wound closure"],
    },

    {
        "id": "fa_close_002",
        "category": "wound_closure",
        "wound_type": "general",
        "title": "Wound Closure with Liquid Bandage",
        "content": (
            "Liquid bandage or skin glue (cyanoacrylate-based) is an effective modern "
            "alternative for closing small, clean minor cuts in areas where regular "
            "bandages are difficult to apply, such as finger knuckles or the bridge of "
            "the nose. Apply only to dry, clean wound edges. Hold the wound edges "
            "together and apply a thin layer of liquid bandage over the top, not inside "
            "the wound. Let it dry for 60 seconds. It typically falls off on its own "
            "within 5 to 10 days. Do not use inside the mouth, near eyes, or on infected "
            "or heavily bleeding wounds."
        ),
        "severity_applicable": "minor",
        "tags": ["liquid bandage", "skin glue", "closure", "cyanoacrylate", "knuckle"],
    },

    # ─── DO's AND DON'Ts SUMMARY RECORDS ────────────────────────────────────────

    {
        "id": "fa_dos_001",
        "category": "dos_and_donts",
        "wound_type": "general",
        "title": "Top First Aid Do's for Minor Wounds",
        "content": (
            "DO wash hands before treating any wound. DO apply firm direct pressure to "
            "stop bleeding. DO clean the wound with running water for at least 5 minutes. "
            "DO apply antiseptic ointment to keep the wound moist and prevent infection. "
            "DO cover the wound with a clean sterile dressing. DO change the dressing "
            "daily. DO monitor for signs of infection such as increasing redness, "
            "swelling, or pus. DO seek medical attention if the wound is large, deep, "
            "or not improving within 3 to 5 days. DO keep the wound protected from "
            "dirt and sun exposure during healing."
        ),
        "severity_applicable": "minor",
        "tags": ["dos", "first aid", "rules", "summary", "wound care"],
    },

    {
        "id": "fa_dos_002",
        "category": "dos_and_donts",
        "wound_type": "general",
        "title": "Top First Aid Don'ts for Minor Wounds",
        "content": (
            "DON'T use hydrogen peroxide or alcohol directly in a wound as they damage "
            "healthy tissue. DON'T remove a dressing that is sticking — soak it with "
            "water first. DON'T pick at scabs, as this delays healing and worsens "
            "scarring. DON'T blow on a wound as breath introduces bacteria. DON'T "
            "apply traditional remedies like turmeric powder, ghee, or toothpaste "
            "directly into wounds. DON'T cover a wound so tightly that circulation "
            "is restricted. DON'T ignore increasing pain or redness after the first "
            "24 hours. DON'T leave a wound uncovered in dusty or outdoor environments."
        ),
        "severity_applicable": "minor",
        "tags": ["donts", "avoid", "mistakes", "rules", "wound care"],
    },

    {
        "id": "fa_dos_003",
        "category": "dos_and_donts",
        "wound_type": "general",
        "title": "First Aid Rules for Wounds on the Face and Head",
        "content": (
            "Face and head wounds need special attention due to high bleeding and visibility. "
            "DO control bleeding with gentle but firm pressure for 15 minutes. DO use "
            "steri-strips instead of bulky dressings on the face for better healing and "
            "less scarring. DO protect healing face wounds from sun exposure strictly "
            "as UV light causes permanent dark pigmentation on new skin. DO check for "
            "signs of concussion after head injuries — nausea, confusion, or unequal pupils. "
            "DON'T apply tight bandage wraps around the head. DON'T use bandages with "
            "strong adhesive on facial skin as removal can tear fragile facial skin."
        ),
        "severity_applicable": "minor",
        "tags": ["face", "head", "rules", "steri-strip", "concussion", "scar"],
    },

]


def get_all_first_aid_documents():
    """Return all first aid documents for RAG ingestion."""
    return FIRST_AID_DOCUMENTS


def get_documents_by_category(category: str):
    """Filter documents by category."""
    return [doc for doc in FIRST_AID_DOCUMENTS if doc["category"] == category]


def get_documents_by_tag(tag: str):
    """Filter documents by a specific tag."""
    return [doc for doc in FIRST_AID_DOCUMENTS if tag in doc.get("tags", [])]


def get_documents_by_body_part(body_part: str):
    """Filter documents relevant to a specific body part via tags."""
    return [doc for doc in FIRST_AID_DOCUMENTS if body_part.lower() in doc.get("tags", [])]


if __name__ == "__main__":
    docs = get_all_first_aid_documents()
    print(f"Total first aid records: {len(docs)}")
    categories = set(doc["category"] for doc in docs)
    print(f"Categories covered: {', '.join(categories)}")
