"""Quick client for Jebadiah running under llama-server.

Reuses the model repo's own prompt renderer and decide helpers, so prompts match training exactly.
Start the server first (.\\start-server.ps1), then:  .venv\\Scripts\\python.exe decide.py
"""
import json
import os
import sys
import time

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "jeb-9b-v2.1")
sys.path.insert(0, os.path.join(MODEL_DIR, "scripts"))
from decide_gguf import label_logprobs, load_renderer, option_probs, read_temperatures  # noqa: E402
from jebadiah_prompt import answer_from_probs  # noqa: E402

SERVER = "http://127.0.0.1:8080"
_renderer = load_renderer(MODEL_DIR)
_temps = read_temperatures(os.path.join(MODEL_DIR, "temperatures.json"))


def decide(state, questions: dict) -> dict:
    """state: str or dict. questions: {id: {type: choice|noul|score, instructions, criteria}}.
    One llama-server pass per question."""
    answers = {}
    for qid, q in questions.items():
        rd = _renderer.render(state, q)
        lps, _ = label_logprobs(SERVER, rd.prompt, rd.cand_ids)
        probs = option_probs(lps, _temps.get(q["type"], 1.0))
        answers[qid] = answer_from_probs(q, rd.keys, probs)
    return answers


if __name__ == "__main__":
    state = {"ticket": "Customer says the invoice total does not match the quote."}
    questions = {
        "route": {"type": "choice", "instructions": "Which team should take this ticket?",
                  "criteria": {"billing": "an invoice, a charge or a refund",
                               "support": "a product question",
                               "sales": "a quote or a renewal"}},
        "urgent": {"type": "noul", "instructions": "The customer is blocked from working.",
                   "criteria": {"true": "work has stopped", "false": "it can wait"}},
    }
    t0 = time.perf_counter()
    print(json.dumps(decide(state, questions), indent=1))
    print(f"took {time.perf_counter() - t0:.1f}s")
