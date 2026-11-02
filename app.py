"""Decision engine UI: one Flask process renders the page and answers /api/decide.

Needs llama-server running (.\\start-server.ps1). Run:  .venv\\Scripts\\python.exe app.py
"""
import json
import time
import urllib.error
import urllib.request

from flask import Flask, jsonify, render_template, request

from decide import SERVER, decide  # also puts the model's scripts/ on sys.path
from ainode_prompt_verbatim import DecideError  # noqa: E402

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
