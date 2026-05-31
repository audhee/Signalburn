"""
step2_generate_sft_pairs.py — Generate high-quality SFT Q&A pairs from structured first aid data.

This script generates Q&A pairs from THREE high-quality structured data sources:
1. first_aid_data.py       — 50+ structured first aid records (wound care, burns, bleeding)
2. harshita_first_aid.json — 200+ real-world Indian first aid scenarios
3. health_data.py          — Vital signs, chronic conditions, emergency response

NO LLM calls needed for answer generation — the data is already well-structured.
Each condition generates 2-5 diverse questions with proper Arohan-style answers.

Usage:
    python step2_generate_sft_pairs.py

Output:
    ./sft_data/sft_pairs_raw.jsonl
"""

import os
import sys
import json
import random
import logging
from pathlib import Path
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(os.path.dirname(BASE_DIR), "app", "knowledge_base")

OUTPUT_DIR = os.path.join(BASE_DIR, "sft_data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "sft_pairs_raw.jsonl")

random.seed(42)

# ── Helpers ──────────────────────────────────────────────────────────────────

def normalize_answer(text: str) -> str:
    """Clean up answer text."""
    text = text.strip()
    # Remove any leading/trailing quotes
    text = text.strip('"').strip("'")
    return text


def format_step_list(steps: List[str]) -> str:
    """Format a list of steps as numbered first aid instructions."""
    if not steps:
        return ""
    numbered = []
    for i, step in enumerate(steps, 1):
        step = step.strip().rstrip(".")
        numbered.append(f"{i}. {step}.")
    return "\n".join(numbered)


def format_emergency(emergency_text: str) -> str:
    """Format emergency guidance."""
    text = emergency_text.strip().rstrip(".")
    # Ensure it mentions calling emergency services
    if "112" not in text and "108" not in text and "emergency" not in text.lower():
        return f"{text}. Call 112 or 108 if condition worsens."
    return f"{text}."


def generate_question_variations(title: str, category: str = "", tags: List[str] = None) -> List[str]:
    """Generate diverse question phrasings for a first aid condition."""
    title_lower = title.lower()
    tags = tags or []

    questions = []

    # Direct question from title
    questions.append(f"What should I do for {title_lower}?")
    questions.append(f"How do I treat {title_lower}?")

    # Body-part based questions
    body_parts = ["head", "finger", "hand", "knee", "foot", "arm", "leg", "face",
                   "toe", "eye", "ear", "nose", "lip", "shoulder", "neck", "back",
                   "chest", "scalp", "palm", "heel"]
    found_parts = [p for p in body_parts if p in title_lower or p in tags]

    # Situation-based questions
    if "burn" in title_lower:
        questions.append(f"I got a {title_lower}. What first aid should I do?")
        if not any("hot water" in title_lower or "oil" in title_lower or "steam" in title_lower for p in found_parts):
            questions.append(f"Help! I have a burn on my skin. What do I do immediately?")
    elif "cut" in title_lower or "bleeding" in title_lower or "wound" in title_lower:
        questions.append(f"I cut myself and it is bleeding. What should I do?")
        questions.append(f"My {found_parts[0] if found_parts else 'skin'} is bleeding after an injury. Please help.")
    elif "choking" in title_lower:
        questions.append(f"Someone is choking on food. What should I do?")
        questions.append(f"A person cannot breathe because something is stuck in their throat. Help!")
    elif "fainting" in title_lower or "unconscious" in title_lower:
        questions.append(f"A person just fainted. What should I do?")
    elif "fracture" in title_lower or "broken" in title_lower:
        questions.append(f"I think I broke my {found_parts[0] if found_parts else 'bone'}. What first aid should I do?")
    elif "sprain" in title_lower or "strain" in title_lower or "twisted" in title_lower:
        questions.append(f"I twisted my {found_parts[0] if found_parts else 'ankle'} and it is swollen. What should I do?")
    elif "bite" in title_lower or "sting" in title_lower:
        questions.append(f"An animal bit me. What first aid should I do?")
        questions.append(f"I got stung by an insect. What should I do?")
    elif "poison" in title_lower:
        questions.append(f"Someone ate something poisonous. What should I do?")
    elif "allergic" in title_lower:
        questions.append(f"I am having an allergic reaction. What should I do?")
    elif "heart" in title_lower or "chest pain" in title_lower:
        questions.append(f"I have chest pain. Is this a heart attack? What should I do?")
    elif "stroke" in title_lower:
        questions.append(f"How do I know if someone is having a stroke? What should I do?")
    elif "fever" in title_lower:
        questions.append(f"My {title_lower}. What should I do?")
    elif "dehydration" in title_lower or "diarrhea" in title_lower or "vomiting" in title_lower:
        questions.append(f"I have {title_lower}. What should I do?")
    elif "asthma" in title_lower or "breathing" in title_lower:
        questions.append(f"I cannot breathe properly. What should I do?")
    elif "splinter" in title_lower or "thorn" in title_lower or "object stuck" in title_lower:
        questions.append(f"Something got stuck in my skin. How do I remove it?")
    elif "seizure" in title_lower or "fit" in title_lower:
        questions.append(f"Someone is having a seizure. What should I do?")
    elif "nose bleed" in title_lower or "nosebleed" in title_lower:
        questions.append(f"My nose is bleeding suddenly. What should I do?")
    elif "shock" in title_lower:
        questions.append(f"A person looks pale and is shaking after an injury. What should I do?")
    elif "electric" in title_lower:
        questions.append(f"Someone got an electric shock. What should I do?")
    elif "drowning" in title_lower:
        questions.append(f"A person was rescued from water and is not breathing. What should I do?")
    elif "cpr" in title_lower or "cardiac" in title_lower:
        questions.append(f"A person collapsed and is not breathing. How do I do CPR?")
    else:
        # Generic questions
        questions.append(f"My {found_parts[0] if found_parts else 'body'} is hurting. What could be wrong?")
        questions.append(f"What is the first aid for {title_lower}?")

    # Add elder-specific variant
    if random.random() < 0.3:
        questions.append(f"I am an elderly person and I have {title_lower}. What should I do carefully?")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in questions:
        q_norm = q.lower().strip()
        if q_norm not in seen:
            seen.add(q_norm)
            unique.append(q)

    return unique


# ── Source 1: first_aid_data.py ──────────────────────────────────────────────

def load_first_aid_data() -> List[Dict]:
    """Load structured first aid records."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(KB_DIR)))
    try:
        from app.knowledge_base.first_aid_data import FIRST_AID_DOCUMENTS
        logger.info(f"Loaded {len(FIRST_AID_DOCUMENTS)} records from first_aid_data.py")
        return FIRST_AID_DOCUMENTS
    except ImportError as e:
        logger.error(f"Could not import first_aid_data: {e}")
        return []


def generate_pairs_from_first_aid_data(records: List[Dict]) -> List[Dict]:
    """Generate Q&A pairs from structured first aid records."""
    pairs = []

    for doc in records:
        title = doc.get("title", "")
        content = doc.get("content", "")
        category = doc.get("category", "")
        tags = doc.get("tags", [])
        severity = doc.get("severity_applicable", "minor")

        # Skip records without meaningful content
        if len(content) < 50:
            continue

        # Generate answer from content — rephrase as numbered steps
        # Split content into logical steps
        sentences = [s.strip() for s in content.replace("\n", " ").split(". ") if len(s.strip()) > 15]

        # Reformat as numbered first aid steps
        if len(sentences) >= 3:
            steps = []
            for i, s in enumerate(sentences[:8], 1):
                s = s.strip()
                if not s.endswith("."):
                    s += "."
                steps.append(f"{i}. {s}")

            answer = "\n".join(steps)

            # Add emergency line if applicable
            if severity == "major":
                answer += "\n\nCall 112 or 108 immediately if condition worsens or does not improve."
            else:
                answer += "\n\nConsult a doctor if the condition does not improve within 24 hours."
        else:
            answer = content
            if severity == "major":
                answer += "\n\nCall 112 or 108 immediately."
            else:
                answer += "\n\nConsult a doctor if needed."

        # Generate 2-3 diverse questions
        questions = generate_question_variations(title, category, tags)

        for q in questions[:3]:  # Max 3 per record
            pairs.append({
                "instruction": q,
                "input": "",
                "output": answer,
                "source": f"first_aid_data/{doc.get('id', title)}",
                "category": category,
                "severity": severity,
            })

    logger.info(f"Generated {len(pairs)} pairs from first_aid_data.py")
    return pairs


# ── Source 2: harshita_first_aid.json ────────────────────────────────────────

def load_harshita_data() -> List[Dict]:
    """Load harshita's first aid JSON."""
    json_path = os.path.join(KB_DIR, "harshita_first_aid.json")
    if not os.path.exists(json_path):
        logger.error(f"harshita_first_aid.json not found at {json_path}")
        return []

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} records from harshita_first_aid.json")
    return data


def generate_pairs_from_harshita_data(records: List[Dict]) -> List[Dict]:
    """Generate Q&A pairs from harshita's structured first aid data."""
    pairs = []

    for doc in records:
        title = doc.get("title", "")
        identify = doc.get("identify", "")
        steps = doc.get("immediate_steps", [])
        avoid_list = doc.get("avoid", [])
        emergency = doc.get("emergency", "")

        # Build Arohan-style answer with numbered steps
        parts = []

        # Identify symptoms
        if identify:
            parts.append(f"{identify}.")

        # Immediate steps
        if steps:
            parts.append("\nWhat to do:")
            for i, step in enumerate(steps, 1):
                s = step.strip().rstrip(".")
                parts.append(f"{i}. {s}.")

        # What to avoid
        if avoid_list:
            parts.append("\nWhat NOT to do:")
            for i, avoid in enumerate(avoid_list, 1):
                a = avoid.strip().rstrip(".")
                parts.append(f"{i}. {a}.")

        # Emergency guidance
        if emergency:
            emergency_text = emergency.strip().rstrip(".")
            if "112" not in emergency_text and "108" not in emergency_text and "emergency" not in emergency_text.lower():
                emergency_text = f"{emergency_text}. Call 112 or 108 if condition worsens or does not improve."
            else:
                emergency_text = f"{emergency_text}."
            parts.append(f"\nWhen to seek help:\n{emergency_text}")

        answer = "\n".join(parts)

        # Generate 2-4 diverse questions per record
        questions = generate_question_variations(title)

        # Filter question count based on record diversity
        max_q = 4 if len(steps) >= 3 else 3

        for q in questions[:max_q]:
            pairs.append({
                "instruction": q,
                "input": "",
                "output": answer,
                "source": f"harshita_first_aid/{title}",
                "category": "first_aid",
                "severity": "varies",
            })

    logger.info(f"Generated {len(pairs)} pairs from harshita_first_aid.json")
    return pairs


# ── Source 3: health_data.py ─────────────────────────────────────────────────

def load_health_data() -> List[str]:
    """Load health knowledge base strings."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(KB_DIR)))
    try:
        from app.knowledge_base.health_data import HEALTH_KNOWLEDGE_BASE
        logger.info(f"Loaded {len(HEALTH_KNOWLEDGE_BASE)} records from health_data.py")
        return HEALTH_KNOWLEDGE_BASE
    except ImportError as e:
        logger.error(f"Could not import health_data: {e}")
        return []


def generate_pairs_from_health_data(records: List[str]) -> List[Dict]:
    """Generate Q&A pairs from health knowledge base strings."""
    pairs = []

    question_map = {
        "blood pressure": [
            "What is normal blood pressure?",
            "What should my blood pressure be?",
            "My blood pressure is high. What should I do?",
            "What are the symptoms of high blood pressure?",
            "How can I manage my blood pressure?",
            "When should I go to the hospital for high blood pressure?",
        ],
        "heart rate": [
            "What is a normal heart rate?",
            "My heart is beating very fast. Should I worry?",
            "My heart rate is very low. Is that dangerous?",
            "What are the symptoms of an abnormal heart rate?",
        ],
        "blood sugar": [
            "What is normal blood sugar level?",
            "What is diabetes? How do I know if I have it?",
            "My blood sugar is low. What should I do?",
            "My blood sugar is very high. What should I do?",
            "How do I manage my blood sugar as a diabetic?",
        ],
        "spO2": [
            "What is a normal oxygen level in blood?",
            "My oxygen level is low. What should I do?",
            "What are the symptoms of low oxygen?",
        ],
        "oxygen": [
            "What is a normal oxygen level in blood?",
            "My oxygen level is low. What should I do?",
            "What are the symptoms of low oxygen?",
        ],
        "cpr": [
            "How do I do CPR on someone who collapsed?",
            "Someone is not breathing. What do I do?",
            "Can you teach me CPR step by step?",
        ],
        "heart attack": [
            "What are the signs of a heart attack?",
            "I think someone is having a heart attack. What should I do?",
            "What are the warning signs of a heart attack?",
        ],
        "stroke": [
            "What are the warning signs of a stroke?",
            "How do I know if someone is having a stroke?",
            "What should I do if someone is having a stroke?",
            "What does FAST mean for stroke?",
        ],
        "emergency": [
            "What number do I call in a medical emergency in India?",
            "Who do I call for an ambulance in India?",
        ],
        "elderly": [
            "What health problems are common in elderly people?",
            "How do I care for an elderly person with dehydration?",
        ],
        "dehydration": [
            "How do I know if an elderly person is dehydrated?",
        ],
    }

    for record in records:
        record_lower = record.lower()

        # Find matching questions
        matched_questions = []
        for keyword, qs in question_map.items():
            if keyword in record_lower:
                matched_questions.extend(qs)

        # Deduplicate
        matched_questions = list(dict.fromkeys(matched_questions))

        # Answer is the record itself
        answer = record

        for q in matched_questions[:3]:
            pairs.append({
                "instruction": q,
                "input": "",
                "output": answer,
                "source": "health_data.py",
                "category": "health_knowledge",
                "severity": "varies",
            })

    logger.info(f"Generated {len(pairs)} pairs from health_data.py")
    return pairs


# ── Source 4: First-aid relevant RAG chunks (filtered) ───────────────────────
# We skip RAG chunks entirely since the structured data covers first aid fully.
# Textbook chunks cause "section X" poisoning as proven by prior eval.


# ── Main Pipeline ────────────────────────────────────────────────────────────

def deduplicate_pairs(pairs: List[Dict]) -> List[Dict]:
    """Remove pairs with near-identical questions."""
    seen_questions = set()
    unique = []

    for p in pairs:
        q_normalized = p["instruction"].lower().strip().rstrip("?").strip()
        if q_normalized not in seen_questions:
            seen_questions.add(q_normalized)
            unique.append(p)

    return unique


def shuffle_and_save(pairs: List[Dict], output_file: str):
    """Shuffle and save pairs to JSONL."""
    random.shuffle(pairs)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for p in pairs:
            # Remove internal fields before saving
            entry = {
                "instruction": p["instruction"],
                "input": p["input"],
                "output": p["output"],
                "source": p.get("source", "unknown"),
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(f"Saved {len(pairs)} pairs to {output_file}")

    # Print source distribution
    sources = {}
    for p in pairs:
        src = p.get("source", "unknown").split("/")[0]
        sources[src] = sources.get(src, 0) + 1
    logger.info("Source distribution:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        logger.info(f"  {count:5d} - {src}")


def run_pipeline():
    """Full generation pipeline."""
    all_pairs = []

    # Source 1: first_aid_data.py
    fa_data = load_first_aid_data()
    if fa_data:
        pairs1 = generate_pairs_from_first_aid_data(fa_data)
        all_pairs.extend(pairs1)
        logger.info(f"  → {len(pairs1)} pairs from first_aid_data.py")

    # Source 2: harshita_first_aid.json
    harshita_data = load_harshita_data()
    if harshita_data:
        pairs2 = generate_pairs_from_harshita_data(harshita_data)
        all_pairs.extend(pairs2)
        logger.info(f"  → {len(pairs2)} pairs from harshita_first_aid.json")

    # Source 3: health_data.py
    health_data = load_health_data()
    if health_data:
        pairs3 = generate_pairs_from_health_data(health_data)
        all_pairs.extend(pairs3)
        logger.info(f"  → {len(pairs3)} pairs from health_data.py")

    # Deduplicate
    logger.info(f"Total before dedup: {len(all_pairs)}")
    all_pairs = deduplicate_pairs(all_pairs)
    logger.info(f"Total after dedup: {len(all_pairs)}")

    # Generate generation log
    stats = {
        "total_pairs": len(all_pairs),
        "method": "programmatic_from_structured_data",
        "sources": {},
    }
    for p in all_pairs:
        src = p.get("source", "unknown").split("/")[0]
        stats["sources"][src] = stats["sources"].get(src, 0) + 1

    log_file = os.path.join(OUTPUT_DIR, "sft_generation_log.json")
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    # Save
    shuffle_and_save(all_pairs, OUTPUT_FILE)

    return all_pairs, stats


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Step 2: Generate SFT Q&A Pairs from Structured First Aid Data")
    print("=" * 60 + "\n")

    pairs, stats = run_pipeline()

    print("\n" + "=" * 60)
    print("  GENERATION COMPLETE")
    print("=" * 60)
    print(f"  Total Q&A pairs:   {stats['total_pairs']}")
    print(f"  Method:            Programmatic (no LLM calls)")
    print(f"\n  Source breakdown:")
    for src, count in sorted(stats["sources"].items(), key=lambda x: -x[1]):
        print(f"    {count:5d} - {src}")
    print(f"\n  Output:            {OUTPUT_FILE}")
    print("\n" + "=" * 60)
    # Keep ASCII-only for Windows consoles that default to cp1252.
    print("  [DONE] Next step: python step3_prepare_dataset.py")
    print("=" * 60 + "\n")
