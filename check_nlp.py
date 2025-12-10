from nlp_utils import interpret_query

tests = [
    "What is my latest BP reading?",
    "How many steps did I walk last week?",
    "Did I reach my goal today?",
    "Show me a summary report",
    "What was my sugar on 2025-12-09?",
    "How many steps today?"
]

for q in tests:
    parsed = interpret_query(q)
    print("Q:", q)
    print("Parsed:", parsed)
    print("-" * 50)