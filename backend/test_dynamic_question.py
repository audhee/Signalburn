import sys
from app.api.v1.ai_routes import get_dynamic_question

def test_questions():
    test_cases = [
        {
            "name": "Stroke Query (checking if 'acute' matches 'cut')",
            "context": "Q: What happened?\nA: i got acute ischemic brain stroke",
            "expected_contains": "weakness"
        },
        {
            "name": "Chest Pain Query",
            "context": "Q: What happened?\nA: I have severe chest pain",
            "expected_contains": "radiating"
        },
        {
            "name": "Actual Bleeding Query",
            "context": "Q: What happened?\nA: I cut my hand and it is bleeding",
            "expected_contains": "bleeding"
        },
        {
            "name": "Collapse Query",
            "context": "Q: What happened?\nA: The person collapsed and is unconscious",
            "expected_contains": "breathing"
        }
    ]
    
    print("Testing Dynamic Question Selector...")
    print("=" * 60)
    for tc in test_cases:
        q = get_dynamic_question(tc["context"], [])
        print(f"Case: {tc['name']}")
        print(f"Context: {tc['context'].replace('\n', ' | ')}")
        print(f"Dynamic Question Generated: '{q}'")
        
        # Simple verification check
        success = tc["expected_contains"] in q.lower()
        print(f"Status: {'PASS' if success else 'FAIL'}")
        print("-" * 60)

if __name__ == "__main__":
    test_questions()
