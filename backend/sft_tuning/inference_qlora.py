"""
inference_qlora.py — Load and test the trained QLoRA adapter locally.

This script can run on any machine (CPU or GPU). It loads the base model
in 4-bit, attaches the LoRA adapter, and runs inference on test queries.

Usage:
    # CPU (slow but works for testing):
    python inference_qlora.py --adapter ./arohan_qlora_adapter/experiment_medium

    # GPU (fast):
    python inference_qlora.py --adapter ./arohan_qlora_adapter/experiment_medium --device cuda

    # With merged model (no adapter needed):
    python inference_qlora.py --merged ./arohan_qlora_adapter/experiment_medium_merged
"""

import os
import sys
import json
import argparse
import torch
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Base model (same as training)
BASE_MODEL = "unsloth/llama-3-8b-Instruct-bnb-4bit"
MAX_SEQ_LENGTH = 2048

# Arohan system prompt
AROHAN_SYSTEM_PROMPT = (
    "You are Arohan, a medical first aid assistant for elderly Indians. "
    "Provide clear, numbered first aid steps using simple words. "
    "Never diagnose conditions. Never recommend prescription medications. "
    "Always suggest consulting a doctor for serious or worsening conditions. "
    "For emergencies, always end with: Call 112 or 108 immediately."
)


def load_model(adapter_path=None, merged_path=None, device="auto"):
    """Load model: adapter-only (base + LoRA) or merged (standalone)."""
    from unsloth import FastLanguageModel

    if merged_path:
        # Load merged model (adapter already merged into base)
        logger.info(f"Loading merged model from: {merged_path}")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=merged_path,
            max_seq_length=MAX_SEQ_LENGTH,
            dtype=None,
            load_in_4bit=(device != "cpu"),
        )
        logger.info("Merged model loaded successfully!")
        return model, tokenizer

    # Load base model
    logger.info(f"Loading base model: {BASE_MODEL}")
    if device == "cpu":
        logger.info("CPU mode: loading in 8-bit to reduce memory")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=BASE_MODEL,
            max_seq_length=MAX_SEQ_LENGTH,
            dtype=torch.float32,
            load_in_4bit=False,
            device_map=None,
        )
    else:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=BASE_MODEL,
            max_seq_length=MAX_SEQ_LENGTH,
            dtype=None,
            load_in_4bit=True,
        )

    if adapter_path:
        # Load LoRA adapter on top of base
        logger.info(f"Loading LoRA adapter from: {adapter_path}")
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter_path)
        logger.info("Adapter loaded successfully!")

    return model, tokenizer


def run_inference(model, tokenizer, query: str, temperature: float = 0.1) -> str:
    """Generate a first aid response for the given query."""
    from unsloth import FastLanguageModel
    FastLanguageModel.for_inference(model)

    messages = [
        {"role": "system", "content": AROHAN_SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    prompt = tokenizer.apply_chat_template(messages, tokenize=False)
    prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=400,
            temperature=temperature,
            do_sample=(temperature > 0),
            top_p=0.9 if temperature > 0 else 1.0,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the assistant's response
    if "assistant" in response:
        response = response.split("assistant")[-1].strip()

    return response


def compare_with_groq(query: str, qlora_response: str):
    """Optionally compare QLoRA response with Groq production response."""
    try:
        from groq import Groq
        client = Groq()

        groq_resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": AROHAN_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.1,
            max_tokens=400,
        )
        groq_text = groq_resp.choices[0].message.content

        logger.info("\n" + "=" * 60)
        logger.info("GROQ COMPARISON (Production)")
        logger.info("=" * 60)
        logger.info(f"\n{groq_text}")
        logger.info("-" * 60)

    except (ImportError, Exception) as e:
        logger.info(f"Groq comparison skipped: {e}")


def main():
    parser = argparse.ArgumentParser(description="Arohan QLoRA Inference")
    parser.add_argument("--adapter", type=str, default=None,
                        help="Path to LoRA adapter directory")
    parser.add_argument("--merged", type=str, default=None,
                        help="Path to merged model directory")
    parser.add_argument("--device", type=str, default="auto",
                        choices=["auto", "cuda", "cpu"],
                        help="Device to run on")
    parser.add_argument("--temperature", type=float, default=0.1,
                        help="Generation temperature")
    parser.add_argument("--compare-groq", action="store_true",
                        help="Also get response from Groq for comparison")
    parser.add_argument("--query", type=str, default=None,
                        help="Single query to test (optional)")
    args = parser.parse_args()

    print("\n" + "#" * 60)
    print("#  Arohan QLoRA Inference")
    print("#  Test your trained PEFT adapter")
    print("#" * 60 + "\n")

    if not args.adapter and not args.merged:
        logger.error("Provide either --adapter or --merged path")
        logger.error("Example: python inference_qlora.py --adapter ./arohan_qlora_adapter/experiment_medium")
        sys.exit(1)

    # Load model
    model, tokenizer = load_model(
        adapter_path=args.adapter,
        merged_path=args.merged,
        device=args.device,
    )

    # Test queries
    test_queries = [
        "What should I do if my nose is bleeding?",
        "Someone fainted and is not responding. What first aid should I give?",
        "How to treat a minor burn from hot oil?",
        "My child swallowed a coin. What should I do?",
        "An elderly person is having chest pain. What first aid steps should I take?",
        "Dog bite on hand — what first aid is needed?",
        "What to do for a snake bite on the leg?",
    ]

    if args.query:
        test_queries = [args.query]

    logger.info(f"Running {len(test_queries)} test queries (temperature={args.temperature})")
    logger.info("-" * 60)

    for query in test_queries:
        logger.info(f"\n🧑 Query: {query}")
        response = run_inference(model, tokenizer, query, args.temperature)
        logger.info(f"🤖 Arohan (QLoRA):")
        for line in response.split("\n"):
            logger.info(f"  {line}")

        if args.compare_groq:
            compare_with_groq(query, response)

        print()  # blank line between queries

    logger.info("=" * 60)
    logger.info("Inference complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
