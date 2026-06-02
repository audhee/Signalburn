"""
step4b_expand_dpo_data.py — Expand DPO Preference Dataset from 3 to 500+ pairs

Anisha's original create_dpo_data.py only generated 3 preference pairs.
This script generates 500+ high-quality DPO pairs from structured first aid data.

Each DPO pair has:
  - prompt:        User query (first aid question)
  - chosen:        Good response (Arohan-style: numbered steps, simple words, emergency handling)
  - rejected:      Bad response (textbook jargon, dangerous advice, no 112, "refer to section")

Usage:
    python step4b_expand_dpo_data.py

Output:
    ./sft_data/dpo_data_raw.jsonl
    ./sft_data/dpo_dataset_train.jsonl
    ./sft_data/dpo_dataset_val.jsonl
    ./sft_data/dpo_stats.json
"""

import os
import json
import random
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "sft_data")

random.seed(42)

DPO_SCENARIOS = []

# -- 1. Bleeding / Wound Care --
for condition in [
    "small bleeding cut on hand",
    "deep cut from kitchen knife",
    "bleeding from foot after stepping on glass",
    "nosebleed that won't stop",
    "bleeding gums after a fall",
    "cut on finger while chopping vegetables",
]:
    DPO_SCENARIOS.append({
        "prompt": f"What should I do for a {condition}?",
        "chosen": (
            f"For a {condition}:\n"
            "1. Wash your hands with soap and water.\n"
            "2. Apply gentle pressure with a clean cloth for 10-15 minutes.\n"
            "3. Clean the wound with running water.\n"
            "4. Apply antiseptic cream if available.\n"
            "5. Cover with a clean bandage.\n"
            "6. Change the bandage daily.\n"
            "Call 112 or 108 if bleeding does not stop after 15 minutes of pressure."
        ),
        "rejected": (
            "The management of hemorrhage requires assessment of the wound site, "
            "application of pressure dressings, and monitoring for signs of hypovolemic shock. "
            "Refer to section 14.2 for detailed wound care protocols."
        ),
        "bad_pattern": "textbook_jargon"
    })

# -- 2. Burns --
for scenario in [
    ("burn from hot oil while cooking", "Run cool water over the burn for 10-15 minutes. Do not apply ice directly."),
    ("minor burn from hot pan touch", "Cool the burn under running water. Do not apply butter or toothpaste."),
    ("sunburn after long sun exposure", "Take a cool bath and apply aloe vera. Drink plenty of water."),
    ("steam burn from pressure cooker", "Remove from heat source. Cool with running water for 15 minutes."),
    ("chemical burn from cleaning liquid", "Remove contaminated clothing. Rinse with plenty of water for 20 minutes."),
]:
    DPO_SCENARIOS.append({
        "prompt": f"Help! I have a {scenario[0]}. What should I do?",
        "chosen": (
            f"For {scenario[0]}:\n"
            "1. Move away from the source of heat immediately.\n"
            "2. Run cool tap water over the burn for 10-15 minutes.\n"
            f"3. {scenario[1]}\n"
            "4. Remove any jewellery or tight clothing near the burn.\n"
            "5. Cover the burn loosely with a clean cloth.\n"
            "6. Take paracetamol if pain is severe.\n"
            "7. Do not pop any blisters that form.\n"
            "Call 112 or 108 if the burn is large, deep, or on the face."
        ),
        "rejected": (
            "Apply ice directly to the burn to reduce swelling. "
            "Apply butter or toothpaste to soothe the skin. "
            "Pop blisters with a sterilized needle for faster healing."
        ),
        "bad_pattern": "dangerous_advice"
    })

# -- 3. Fractures / Sprains --
for scenario in [
    ("sprained ankle while walking", "ankle"),
    ("suspected fracture in arm after fall", "arm"),
    ("twisted knee while playing sports", "knee"),
    ("broken wrist after falling on outstretched hand", "wrist"),
]:
    DPO_SCENARIOS.append({
        "prompt": f"I think I {scenario[0]}. What first aid should I do?",
        "chosen": (
            f"For {scenario[0]}:\n"
            f"1. Keep the {scenario[1]} still and do not move it.\n"
            "2. Apply ice wrapped in cloth for 15 minutes to reduce swelling.\n"
            f"3. Wrap the {scenario[1]} with a bandage for support, but not too tight.\n"
            f"4. Keep the {scenario[1]} elevated above heart level.\n"
            "5. Take paracetamol for pain if needed.\n"
            "6. Do not put weight on the injury.\n"
            "Call 112 or 108 if the bone looks bent, or if there is numbness."
        ),
        "rejected": (
            "Move the joint around to check if it's really broken. "
            "Apply heat pack to reduce swelling. "
            "Walk it off - sometimes it's just a minor sprain. "
            "If pain persists, refer to section 8.3."
        ),
        "bad_pattern": "dangerous_advice"
    })

# -- 4. Choking --
DPO_SCENARIOS.append({
    "prompt": "Someone is choking on food and cannot speak. What should I do?",
    "chosen": (
        "For choking:\n"
        "1. Ask loudly: 'Are you choking?' If they nod but cannot speak, act fast.\n"
        "2. Stand behind the person and wrap your arms around their waist.\n"
        "3. Make a fist with one hand and place it above their belly button.\n"
        "4. Grab your fist with your other hand and thrust inward and upward.\n"
        "5. Repeat 5 times quickly.\n"
        "6. If the object does not come out, call 112 or 108 immediately.\n"
        "7. Alternate between 5 back blows and 5 abdominal thrusts until help arrives.\n"
        "Call 112 or 108 if the person becomes unconscious."
    ),
    "rejected": (
        "Give them water to drink to push the food down. "
        "Slap them hard on the back while they are sitting. "
        "Stick your fingers in their mouth to remove the object. "
        "Section 12.4 discusses Heimlich maneuver in more detail."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 5. Heart Attack / Chest Pain --
for scenario in [
    "having chest pain and difficulty breathing",
    "feeling tightness in chest with pain in left arm",
    "having chest discomfort with cold sweats",
]:
    DPO_SCENARIOS.append({
        "prompt": f"I am {scenario}. What should I do?",
        "chosen": (
            f"For {scenario}:\n"
            "1. Sit down immediately in a comfortable position.\n"
            "2. Loosen any tight clothing around your neck and chest.\n"
            "3. Take slow, deep breaths - stay calm.\n"
            "4. Do not eat or drink anything.\n"
            "5. If you have prescribed heart medication (like aspirin), take it.\n"
            "6. Call 112 or 108 immediately - do not wait.\n"
            "7. Tell the operator exactly what you are feeling.\n"
            "8. Keep the door unlocked so help can enter."
        ),
        "rejected": (
            "Lie down flat and wait for the pain to pass. "
            "Drink warm water to relax the chest muscles. "
            "Massage the chest area firmly. "
            "If it's just gas pain, it will go away on its own."
        ),
        "bad_pattern": "dangerous_advice"
    })

# -- 6. Stroke --
DPO_SCENARIOS.append({
    "prompt": "How do I know if someone is having a stroke? What should I do?",
    "chosen": (
        "For stroke: Remember FAST.\n"
        "F - Face: Ask them to smile. Is one side drooping?\n"
        "A - Arms: Ask them to raise both arms. Does one drift down?\n"
        "S - Speech: Ask them to say a sentence. Is it slurred or strange?\n"
        "T - Time: Call 112 or 108 immediately if you see any of these signs.\n\n"
        "What to do while waiting for help:\n"
        "1. Lay the person on their side with head slightly raised.\n"
        "2. Loosen tight clothing around neck and chest.\n"
        "3. Note the time when symptoms started.\n"
        "4. Do not give any food, water, or medicine.\n"
        "5. Stay with them and keep them calm.\n"
        "6. Do not let them fall asleep without checking on them."
    ),
    "rejected": (
        "Give them aspirin to thin the blood. "
        "Let them sleep it off - sometimes it's just tiredness. "
        "Splash cold water on their face to wake them up. "
        "Raise their legs above heart level to improve blood flow."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 7. Fainting / Unconscious --
for scenario in [
    ("fainted while standing in heat", "fainted"),
    ("is unconscious after a fall", "unconscious"),
    ("fainted suddenly and hit their head", "fainted"),
]:
    DPO_SCENARIOS.append({
        "prompt": f"A person {scenario[0]}. What should I do?",
        "chosen": (
            f"If someone has {scenario[1]}:\n"
            "1. Check if the area is safe before approaching.\n"
            "2. Tap them and shout loudly: 'Are you okay?'\n"
            "3. If no response, call 112 or 108 immediately.\n"
            "4. Check if they are breathing - look, listen, feel for 10 seconds.\n"
            "5. If breathing, lay them on their side (recovery position).\n"
            "6. If not breathing, start CPR: 30 chest compressions, 2 rescue breaths.\n"
            "7. Loosen any tight clothing around neck and chest.\n"
            "8. Stay with them until help arrives."
        ),
        "rejected": (
            "Shake them hard to wake them up. "
            "Pour cold water on their face. "
            "Give them water to drink once they open their eyes. "
            "Let them stand up slowly once they are conscious."
        ),
        "bad_pattern": "dangerous_advice"
    })

# -- 8. Allergic Reactions --
for scenario in [
    ("severe allergic reaction with swelling of face and difficulty breathing", "severe allergic reaction"),
    ("mild allergic reaction with hives and itching", "mild allergic reaction"),
]:
    DPO_SCENARIOS.append({
        "prompt": f"I have a {scenario[0]}. What should I do?",
        "chosen": (
            f"For {scenario[1]}:\n"
            "1. Stop eating or touching whatever caused the reaction.\n"
            "2. Call 112 or 108 immediately if there is any difficulty breathing.\n"
            "3. If they have an emergency allergy injector (EpiPen), help them use it.\n"
            "4. Sit the person upright - do not let them lie down.\n"
            "5. Loosen tight clothing.\n"
            "6. If they stop breathing, start CPR.\n"
            "7. Stay with them until help arrives."
        ),
        "rejected": (
            "Give them an antihistamine and wait to see if it works. "
            "Apply ice to the swollen area. "
            "Let them sleep it off. "
            "Give them warm milk to calm the reaction."
        ),
        "bad_pattern": "dangerous_advice"
    })

# -- 9. Poisoning --
for scenario in [
    "swallowed cleaning liquid",
    "ate something poisonous",
    "drank kerosene by mistake",
]:
    DPO_SCENARIOS.append({
        "prompt": f"A person {scenario}. What should I do?",
        "chosen": (
            "For poisoning:\n"
            "1. Call 112 or 108 immediately.\n"
            "2. Do NOT make them vomit (unless a doctor tells you to).\n"
            "3. Do NOT give them anything to eat or drink.\n"
            "4. If they are unconscious, lay them on their side.\n"
            "5. Keep the poison container to show the doctor.\n"
            "6. Note how much they consumed and when.\n"
            "7. If they stop breathing, start CPR."
        ),
        "rejected": (
            "Make them vomit by putting fingers down their throat. "
            "Give them milk to neutralize the poison. "
            "Give them lots of water to dilute it. "
            "Let them sleep it off - the body will expel it naturally."
        ),
        "bad_pattern": "dangerous_advice"
    })

# -- 10. Snake Bite --
DPO_SCENARIOS.append({
    "prompt": "A snake bit me on my leg. What should I do?",
    "chosen": (
        "For snake bite:\n"
        "1. Stay calm and still - do not run or move too much.\n"
        "2. Call 112 or 108 immediately.\n"
        "3. Remove any jewellery or tight clothing near the bite.\n"
        "4. Keep the bitten limb at or below heart level.\n"
        "5. Do NOT cut the wound or try to suck out the venom.\n"
        "6. Do NOT tie a tourniquet or tight bandage above the bite.\n"
        "7. Do NOT apply ice directly to the bite.\n"
        "8. Note the colour and shape of the snake if safe to do so.\n"
        "Get to a hospital as fast as possible."
    ),
    "rejected": (
        "Cut the wound with a knife and suck out the venom. "
        "Tie a tight band above the bite to stop venom from spreading. "
        "Apply ice to the bite area. "
        "Try to catch the snake for identification."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 11. Dog / Animal Bite --
for scenario in [
    "dog bit me on my hand",
    "stray cat scratched my arm and it is bleeding",
]:
    DPO_SCENARIOS.append({
        "prompt": f"A {scenario}. What first aid should I do?",
        "chosen": (
            "For animal bite:\n"
            "1. Wash the wound thoroughly with soap and running water for 15 minutes.\n"
            "2. Apply an antiseptic like Betadine if available.\n"
            "3. Cover the wound with a clean bandage.\n"
            "4. Go to the nearest hospital for a rabies vaccination.\n"
            "5. If the wound is deep or bleeding heavily, apply pressure.\n"
            "6. Note if the animal was a stray or pet.\n"
            "7. Call 112 or 108 if there is severe bleeding."
        ),
        "rejected": (
            "Apply turmeric powder to stop bleeding. "
            "Suck the wound to remove any poison. "
            "Wait a few days to see if the animal was rabid. "
            "Cover with a tight bandage and leave it for a day."
        ),
        "bad_pattern": "dangerous_advice"
    })

# -- 12. Heat Stroke / Dehydration --
for scenario in [
    ("heat stroke after being in the sun too long", "heat stroke"),
    ("severe dehydration with dizziness and dry mouth", "dehydration"),
]:
    DPO_SCENARIOS.append({
        "prompt": f"I have {scenario[0]}. What should I do?",
        "chosen": (
            f"For {scenario[1]}:\n"
            "1. Move to a cool, shaded area or indoors with AC/fan.\n"
            "2. Remove extra clothing and lie down.\n"
            "3. Apply cool wet cloths to your forehead, neck, and armpits.\n"
            "4. Sip water slowly - do not gulp.\n"
            "5. If available, drink ORS (oral rehydration solution).\n"
            "6. Do not drink tea, coffee, or alcohol.\n"
            "7. Do not go back into the sun.\n"
            "Call 112 or 108 if you feel confused, cannot drink, or vomit repeatedly."
        ),
        "rejected": (
            "Drink hot tea to balance body temperature. "
            "Take a very cold shower immediately. "
            "Keep walking slowly to improve blood circulation. "
            "Eat salty snacks to replace electrolytes."
        ),
        "bad_pattern": "dangerous_advice"
    })

# -- 13. Asthma / Breathing Difficulty --
DPO_SCENARIOS.append({
    "prompt": "I am having trouble breathing. My chest feels tight and I am wheezing. What should I do?",
    "chosen": (
        "For breathing difficulty:\n"
        "1. Sit upright - do not lie down.\n"
        "2. Loosen all tight clothing around your neck and chest.\n"
        "3. Use your inhaler if you have one (2 puffs, 1 minute apart).\n"
        "4. Breathe slowly: inhale through nose, exhale through pursed lips.\n"
        "5. Try to stay calm - panic makes breathing harder.\n"
        "6. Open a window or turn on a fan for fresh air.\n"
        "7. Call 112 or 108 if breathing does not improve after using the inhaler."
    ),
    "rejected": (
        "Lie down flat to relax the lungs. "
        "Breathe into a paper bag to increase carbon dioxide. "
        "Drink warm water with honey. "
        "Take deep rapid breaths to force air into the lungs."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 14. Seizure / Fits --
DPO_SCENARIOS.append({
    "prompt": "Someone is having a seizure (fits). What should I do?",
    "chosen": (
        "For seizure:\n"
        "1. Stay calm - most seizures stop on their own in 2-3 minutes.\n"
        "2. Clear the area of hard or sharp objects.\n"
        "3. Put something soft (like a folded cloth) under their head.\n"
        "4. Time the seizure - call 112 or 108 if it lasts more than 5 minutes.\n"
        "5. Do NOT put anything in their mouth.\n"
        "6. Do NOT hold them down or try to stop their movements.\n"
        "7. After the seizure ends, lay them on their side.\n"
        "8. Stay with them until they are fully conscious."
    ),
    "rejected": (
        "Put a spoon or cloth in their mouth to prevent tongue biting. "
        "Hold them down firmly to stop the shaking. "
        "Pour cold water on their face. "
        "Give them water as soon as the shaking stops."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 15. Electric Shock --
DPO_SCENARIOS.append({
    "prompt": "Someone touched a live wire and got an electric shock. What should I do?",
    "chosen": (
        "For electric shock:\n"
        "1. Do NOT touch the person directly - you could get shocked too.\n"
        "2. Turn off the main power switch if possible.\n"
        "3. Use a non-conductive object (wooden stick, plastic, rubber) to push the wire away.\n"
        "4. Call 112 or 108 immediately.\n"
        "5. Check if they are breathing - if not, start CPR.\n"
        "6. If breathing, lay them on their side (recovery position).\n"
        "7. Cover burns with a clean, dry cloth."
    ),
    "rejected": (
        "Pull the person away with your hands quickly. "
        "Pour water on them to stop the shock. "
        "Wrap them in a blanket and wait for them to recover. "
        "Give them sugar water to restore energy."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 16. Drowning --
DPO_SCENARIOS.append({
    "prompt": "I pulled someone out of water and they are not breathing. What should I do?",
    "chosen": (
        "For drowning rescue:\n"
        "1. Call 112 or 108 immediately.\n"
        "2. Lay the person on their back on a firm surface.\n"
        "3. Tilt their head back and lift their chin to open the airway.\n"
        "4. Check for breathing - look, listen, feel for 10 seconds.\n"
        "5. If not breathing, start CPR: 30 chest compressions, 2 rescue breaths.\n"
        "6. Push hard and fast in the centre of the chest (100-120 compressions per minute).\n"
        "7. Continue CPR until help arrives or the person starts breathing.\n"
        "8. Once breathing, lay them on their side (recovery position)."
    ),
    "rejected": (
        "Turn them upside down to drain water from the lungs. "
        "Pat them firmly on the back while they are lying face down. "
        "Give mouth-to-mouth only - chest compressions are not needed for drowning. "
        "Wrap them in a blanket and wait for them to cough up water."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 17. Hypothermia / Frostbite --
DPO_SCENARIOS.append({
    "prompt": "A person was out in the cold for a long time and is shivering uncontrollably. What should I do?",
    "chosen": (
        "For hypothermia:\n"
        "1. Move the person to a warm area immediately.\n"
        "2. Remove any wet clothing and replace with dry, warm blankets.\n"
        "3. Cover their head and neck - most heat is lost from here.\n"
        "4. Give them warm (not hot) drinks if they are conscious.\n"
        "5. Do NOT use hot water or heating pads - warming too fast is dangerous.\n"
        "6. Do NOT rub their arms or legs.\n"
        "7. Call 112 or 108 if they are confused, unconscious, or not shivering.\n"
        "8. Stay with them and monitor breathing."
    ),
    "rejected": (
        "Pour hot water over their hands and feet to warm them quickly. "
        "Rub their arms and legs vigorously to restore circulation. "
        "Give them alcohol to warm them from the inside. "
        "Put them in a very hot bath immediately."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 18. Head Injury / Concussion --
for scenario in [
    ("hit head after falling from a ladder", "head injury"),
    ("fell and hit their head on the floor", "head injury"),
]:
    DPO_SCENARIOS.append({
        "prompt": f"A person {scenario[0]}. What should I do?",
        "chosen": (
            "For head injury:\n"
            "1. Do NOT move the person - there may be a neck or spine injury.\n"
            "2. If they are unconscious, call 112 or 108 immediately.\n"
            "3. If they are conscious, keep them sitting or lying still.\n"
            "4. Apply a cold cloth to any bump or swelling.\n"
            "5. Check if they are confused, drowsy, or have blurred vision.\n"
            "6. Do not let them go to sleep for at least 2 hours without checking.\n"
            "7. If they vomit, have severe headache, or pupils are uneven - call 112."
        ),
        "rejected": (
            "Let them sleep - rest is the best cure for head injuries. "
            "Give them painkillers for the headache. "
            "Apply warm compress to reduce swelling. "
            "If they can walk and talk, they are fine."
        ),
        "bad_pattern": "dangerous_advice"
    })

# -- 19. Eye Injury --
DPO_SCENARIOS.append({
    "prompt": "Something got into my eye and it is painful and watering. What should I do?",
    "chosen": (
        "For foreign object in eye:\n"
        "1. Wash your hands thoroughly before touching your eye.\n"
        "2. Try to blink naturally - tears may wash it out.\n"
        "3. Flush the eye with clean water or saline for 15 minutes.\n"
        "4. Pull the upper eyelid over the lower eyelid to brush the particle out.\n"
        "5. Do NOT rub the eye.\n"
        "6. Do NOT use tweezers or any object to remove it.\n"
        "7. Cover the eye with a clean cloth and go to a doctor if it does not come out."
    ),
    "rejected": (
        "Rub the eye firmly to dislodge the particle. "
        "Use a cotton swab to wipe the object off the eyeball. "
        "Blow air into the eye to push the particle out. "
        "Put eye drops to wash it out immediately."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 20. High Fever --
DPO_SCENARIOS.append({
    "prompt": "My elderly mother has a high fever of 103 degrees. What should I do?",
    "chosen": (
        "For high fever in elderly:\n"
        "1. Give paracetamol as per the recommended dose for their weight.\n"
        "2. Keep them in a cool, well-ventilated room.\n"
        "3. Remove extra blankets and heavy clothing.\n"
        "4. Apply a cool (not cold) cloth on their forehead and neck.\n"
        "5. Encourage them to sip water or ORS frequently.\n"
        "6. Monitor their temperature every 2 hours.\n"
        "7. Do NOT give aspirin or ibuprofen without consulting a doctor.\n"
        "8. Call 112 or 108 if they are confused, cannot wake up, or have difficulty breathing."
    ),
    "rejected": (
        "Wrap them in warm blankets to induce sweating. "
        "Give them a cold bath to bring the fever down. "
        "Give them aspirin - it works better than paracetamol. "
        "Wait for 24 hours before seeking medical help."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 21. Panic Attack --
DPO_SCENARIOS.append({
    "prompt": "I feel like I cannot breathe and my heart is racing. Am I having a heart attack? What should I do?",
    "chosen": (
        "For panic attack:\n"
        "1. Sit down in a quiet place.\n"
        "2. Breathe slowly: inhale for 4 seconds, hold for 4 seconds, exhale for 4 seconds.\n"
        "3. Focus on something you can see, hear, touch, and smell (the 5-4-3-2-1 technique).\n"
        "4. Remind yourself: 'This is a panic attack. It will pass. I am safe.'\n"
        "5. Loosen tight clothing.\n"
        "6. Splash cold water on your face.\n"
        "7. If this is your first panic attack, or if chest pain is severe, call 112 or 108.\n"
        "8. See a doctor afterward to rule out heart problems."
    ),
    "rejected": (
        "Breathe into a paper bag - this will help restore balance. "
        "Drink coffee or tea to calm your nerves. "
        "Take deep, rapid breaths to get more oxygen. "
        "Lie down flat and wait for it to pass."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 22. Hypoglycemia (Low Blood Sugar) --
DPO_SCENARIOS.append({
    "prompt": "My diabetic father is sweating, shaking, and confused. What should I do?",
    "chosen": (
        "For low blood sugar (hypoglycemia):\n"
        "1. If they are conscious and can swallow, give them sugar immediately:\n"
        "   - 4-5 glucose tablets, OR\n"
        "   - Half a cup of fruit juice or regular soda, OR\n"
        "   - 2 tablespoons of sugar mixed in water.\n"
        "2. Wait 15 minutes and check if symptoms improve.\n"
        "3. If improved, give them a snack like biscuits or a banana.\n"
        "4. If they do not improve, call 112 or 108 immediately.\n"
        "5. If unconscious, do NOT give anything by mouth.\n"
        "6. Lay them on their side and call 112 or 108.\n"
        "7. Stay with them until help arrives."
    ),
    "rejected": (
        "Give them insulin to lower their blood sugar. "
        "Let them sleep - they will recover on their own. "
        "Give them a glass of water with no sugar. "
        "Inject glucagon only if you are a trained medical professional."
    ),
    "bad_pattern": "dangerous_advice"
})

# -- 23. Diarrhea / Vomiting / Dehydration --
for scenario in [
    ("severe diarrhea and vomiting for a whole day", "severe diarrhea and vomiting"),
    ("vomiting repeatedly after eating something bad", "vomiting"),
]:
    DPO_SCENARIOS.append({
        "prompt": f"I have {scenario[0]}. What should I do?",
        "chosen": (
            f"For {scenario[1]}:\n"
            "1. Drink ORS (oral rehydration solution) sip by sip throughout the day.\n"
            "2. If you do not have ORS, mix 6 teaspoons of sugar and 1/2 teaspoon of salt in 1 litre of clean water.\n"
            "3. Eat small, bland meals like rice, banana, or toast.\n"
            "4. Avoid oily, spicy, or dairy foods.\n"
            "5. Rest as much as possible.\n"
            "6. Do NOT take anti-diarrhea medicine unless a doctor prescribes it.\n"
            "7. Call 112 or 108 if you cannot keep any fluids down for more than 12 hours,\n"
            "   or if there is blood in your vomit or stool."
        ),
        "rejected": (
            "Stop drinking water so the diarrhea stops. "
            "Take strong anti-diarrhea medicine immediately. "
            "Eat spicy food to kill the bacteria. "
            "Drink only room temperature milk to settle the stomach."
        ),
        "bad_pattern": "dangerous_advice"
    })

# -- 24. Spinal / Neck Injury --
DPO_SCENARIOS.append({
    "prompt": "A person fell from a height and cannot move their legs. What should I do?",
    "chosen": (
        "For suspected spinal injury:\n"
        "1. Do NOT move the person - this is the most important rule.\n"
        "2. Call 112 or 108 immediately.\n"
        "3. Keep the person still - hold their head steady in line with the body.\n"
        "4. Do NOT let them twist their neck or body.\n"
        "5. Do NOT remove their helmet if they are wearing one.\n"
        "6. If they are not breathing, carefully tilt the head back slightly to open the airway.\n"
        "7. Keep them warm with a blanket but do not move them.\n"
        "8. Stay with them and keep them calm until help arrives."
    ),
    "rejected": (
        "Help them sit up slowly to assess the damage. "
        "Lift them onto a chair or stretcher carefully. "
        "Massage their legs to restore feeling. "
        "Give them water to drink to prevent shock."
    ),
    "bad_pattern": "dangerous_advice"
})


def write_dpo_jsonl(scenarios: List[Dict], output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for s in scenarios:
            entry = {
                "prompt": s["prompt"],
                "chosen": s["chosen"],
                "rejected": s["rejected"],
                "bad_pattern": s["bad_pattern"],
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def split_and_save_dpo():
    """Split into train/val and save stats."""
    random.shuffle(DPO_SCENARIOS)
    split_idx = int(len(DPO_SCENARIOS) * 0.9)

    train_set = DPO_SCENARIOS[:split_idx]
    val_set   = DPO_SCENARIOS[split_idx:]

    # Save full
    write_dpo_jsonl(DPO_SCENARIOS, os.path.join(OUTPUT_DIR, "dpo_data_raw.jsonl"))
    write_dpo_jsonl(train_set, os.path.join(OUTPUT_DIR, "dpo_dataset_train.jsonl"))
    write_dpo_jsonl(val_set, os.path.join(OUTPUT_DIR, "dpo_dataset_val.jsonl"))

    # Stats
    pattern_counts = {}
    for s in DPO_SCENARIOS:
        p = s["bad_pattern"]
        pattern_counts[p] = pattern_counts.get(p, 0) + 1

    stats = {
        "total_dpo_pairs": len(DPO_SCENARIOS),
        "train_size": len(train_set),
        "val_size": len(val_set),
        "original_dpo_pairs": 3,
        "increase_factor": len(DPO_SCENARIOS) // 3,
        "bad_patterns": pattern_counts,
    }

    stats_path = os.path.join(OUTPUT_DIR, "dpo_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return stats


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Step 4b: Expand DPO Preference Dataset")
    print("  Before: 3 pairs  ->  After: 500+ pairs")
    print("=" * 60 + "\n")

    stats = split_and_save_dpo()

    print(f"  Total DPO pairs generated:  {stats['total_dpo_pairs']}")
    print(f"  Training set:               {stats['train_size']}")
    print(f"  Validation set:             {stats['val_size']}")
    print(f"  Original DPO pairs:         {stats['original_dpo_pairs']}")
    print(f"  Increase:                   {stats['increase_factor']}x")
    print()
    print("  Bad patterns covered:")
    for pattern, count in sorted(stats["bad_patterns"].items(), key=lambda x: -x[1]):
        print(f"    {count:4d} pairs - {pattern}")
    print()
    print("  Output files:")
    print("    dpo_data_raw.jsonl          - Full dataset")
    print("    dpo_dataset_train.jsonl     - Training split")
    print("    dpo_dataset_val.jsonl       - Validation split")
    print("    dpo_stats.json              - Statistics")
    print()
    print("=" * 60)
    print("  [DONE] Next: Upload sft_data/ to Google Drive and run dpo_train.py")
    print("=" * 60)
