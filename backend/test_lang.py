import sys
sys.path.insert(0, '.')

from app.services.ai.language_service import detect_language

tests = [
    ("KANNADA", "\u0ca8\u0ca8\u0ccd\u0ca8 \u0cae\u0cc2\u0c97\u0cbf\u0ca8\u0cbf\u0c82\u0ca6 \u0cb0\u0c95\u0ccd\u0ca4 \u0cac\u0cb0\u0cc1\u0ca4\u0ccd\u0ca4\u0cbf\u0ca6\u0cc7"),
    ("HINDI", "\u092e\u0947\u0930\u0940 \u0928\u093e\u0915 \u0938\u0947 \u0916\u0942\u0928 \u092c\u0939 \u0930\u0939\u093e \u0939\u0948"),
    ("HINGLISH", "meri nose se bleeding ho rahi hai"),
    ("KANGLISH", "nanna nose inda bleeding aagutide"),
    ("ENGLISH", "my nose is bleeding"),
]

for name, text in tests:
    result = detect_language(text)
    print(f"{name}: {result['language_code']} ({result['language_name']})")
