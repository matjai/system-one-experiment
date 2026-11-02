"""Decision engine UI: one Flask process renders the page and answers /api/decide.

Needs llama-server running (.\\start-server.ps1). Run:  .venv\\Scripts\\python.exe app.py
decide() is importable on its own for scripts (see quick_test.py).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

from flask import Flask, jsonify, render_template, request

# The model repo ships its own prompt renderer and decide helpers; reuse them so prompts match training exactly.
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "jeb-9b-v2.1")
sys.path.insert(0, os.path.join(MODEL_DIR, "scripts"))
from ainode_prompt_verbatim import DecideError  # noqa: E402
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


app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/decide")
def api_decide():
    body = request.get_json(silent=True) or {}
    state = body.get("state", "")
    if isinstance(state, str) and body.get("state_is_json"):
        try:
            state = json.loads(state)
        except ValueError as e:
            return jsonify(error=f"Context isn't valid JSON: {e}"), 400
    question = body.get("question")
    t0 = time.perf_counter()
    try:
        answer = decide(state, {"q": question})["q"]
    except DecideError as e:
        return jsonify(error=str(e)), 400
    except urllib.error.URLError:
        return jsonify(error=f"Can't reach llama-server at {SERVER}. Start it with .\\start-server.ps1"), 503
    return jsonify(answer=answer, seconds=round(time.perf_counter() - t0, 2))


@app.get("/api/health")
def health():
    try:
        with urllib.request.urlopen(SERVER + "/health", timeout=2) as r:
            return jsonify(engine=json.loads(r.read()).get("status", "unknown"))
    except (urllib.error.URLError, OSError):
        return jsonify(engine="down")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False, threaded=False)
