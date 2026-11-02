"""Three everyday sanity checks, one per question type."""
import json
import time

from decide import decide

tests = [
    ("noul", "The sky on a clear afternoon.", {
        "sky_blue": {"type": "noul", "instructions": "Is the sky color blue?",
                     "criteria": {"true": "the sky is blue", "false": "the sky is not blue"}}}),
    ("choice", "It is raining heavily outside and I need to walk to the shop.", {
        "bring": {"type": "choice", "instructions": "What should I bring?",
                  "criteria": {"umbrella": "keeps you dry in rain",
                               "sunglasses": "protects eyes from bright sun",
                               "fan": "cools you down in hot weather"}}}),
    ("score", "I skipped breakfast and lunch and it is now 4pm.", {
        "hunger": {"type": "score", "instructions": "How hungry am I likely to be?",
                   "criteria": ["not hungry", "a little hungry", "hungry", "very hungry"]}}),
]

for kind, state, questions in tests:
    t0 = time.perf_counter()
    ans = decide(state, questions)
    print(f"--- {kind} ({time.perf_counter() - t0:.1f}s) state: {state}")
    print(json.dumps(ans, indent=1))
