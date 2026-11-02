# System One experiment

A small local playground for a "System One" style decision model: instead of generating text, the model answers
typed questions with a probability over the options you give it, in one forward pass.

It runs [Jebadiah 9B v2.1](https://huggingface.co/frontier-infra/jebadiah-9b-v2-1-GGUF) (Q4_K_M GGUF, Apache-2.0)
on CPU through llama.cpp's `llama-server`, with a single-page Flask + Jinja + Alpine.js UI on top.

## Question types

| Type | You give | You get back |
|---|---|---|
| `noul` (yes/no) | a question, optional meaning of true/false | P(true) |
| `choice` | a question and 2–20 named options (descriptions optional) | the chosen option, confidence, probability per option |
| `score` | a question and 2–10 ordered levels, lowest first | expected level, probability per level |

Every question is judged against a **context** (the "state"): plain text or JSON, up to 2,048 tokens.

## Setup (Windows)

The model is not in this repo; it comes straight from Hugging Face. You need about 6 GB of disk.

### Option A: setup script

Needs [uv](https://docs.astral.sh/uv/). Creates `.venv`, downloads the llama.cpp CPU build and the model, and checks
the model's SHA-256:

```powershell
.\setup.ps1
```

### Option B: manual

1. **Python environment** (Python 3.10+):

   ```powershell
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```

2. **llama.cpp:** download `llama-b12032-bin-win-cpu-x64.zip` from the
   [llama.cpp b12032 release](https://github.com/ggml-org/llama.cpp/releases/tag/b12032) and unzip it into
   `tools\llama.cpp\` so that `tools\llama.cpp\llama-server.exe` exists. Use the CUDA or Vulkan build instead if you
   have a GPU.

3. **Model:** from [frontier-infra/jebadiah-9b-v2-1-GGUF](https://huggingface.co/frontier-infra/jebadiah-9b-v2-1-GGUF)
   download into `models\jeb-9b-v2.1\`:
   - `jebadiah-9b-v2-1-Q4_K_M.gguf` (5.78 GB)
   - the `scripts\` folder
   - `tokenizer.json`, `tokenizer_config.json`, `chat_template.jinja`, `temperatures.json`

   Or with the Hugging Face CLI:

   ```powershell
   .venv\Scripts\hf download frontier-infra/jebadiah-9b-v2-1-GGUF `
       --include "jebadiah-9b-v2-1-Q4_K_M.gguf" --include "scripts/*" --include "*.json" `
       --include "*.jinja" --include "*.txt" --local-dir models\jeb-9b-v2.1
   ```

   Expected SHA-256 of the GGUF: `cb29828caeba5d379e61e7606a988fcc13c4b6f6c77610155dcea1ed7a968e2b`
   (check with `Get-FileHash models\jeb-9b-v2.1\jebadiah-9b-v2-1-Q4_K_M.gguf`).

The resulting layout:

```
models\jeb-9b-v2.1\jebadiah-9b-v2-1-Q4_K_M.gguf
models\jeb-9b-v2.1\scripts\decide_gguf.py, jebadiah_prompt.py, ...
models\jeb-9b-v2.1\tokenizer.json, temperatures.json, ...
tools\llama.cpp\llama-server.exe
```

## Run

1. **Start the engine** (terminal 1). Runs `llama-server` on `127.0.0.1:8080`, CPU only, 4096 context, 4 threads
   (`-Threads 8` to change). Wait for `listening on http://127.0.0.1:8080`:

   ```powershell
   .\start-server.ps1
   ```

2. **Start the UI** (terminal 2), then open http://127.0.0.1:5050:

   ```powershell
   .venv\Scripts\python.exe app.py
   ```

3. **Quick test** without the UI (engine must be running):

   ```powershell
   .venv\Scripts\python.exe quick_test.py
   ```

Or from your own Python script (run from the repo folder):

```python
from app import decide

decide("It is raining heavily and I need to walk to the shop.", {
    "bring": {"type": "choice", "instructions": "What should I bring?",
              "criteria": {"umbrella": "keeps you dry in rain", "sunglasses": None, "fan": None}},
})
```

## How it works

`llama-server` knows nothing about decisions. For each question, `decide()` in `app.py` uses the model repo's own renderer to
build the exact training prompt, asks `/completion` for the probabilities of the next token, keeps only the option
labels (`A`, `B`, …), renormalises them and applies the model's calibration temperatures.

## Example: routing a message

Put the user's message in the context and ask a `choice` question:

- **Question:** How should the assistant get the information needed to answer this message?
- **Options:**
  - `direct`: general knowledge, reasoning, writing or casual chat the assistant can answer on its own
  - `knowledge`: needs our internal company documents, policies, products or past records
  - `web`: needs current or recent information from the internet, such as news, prices, weather or live events

On test messages this picked the expected route at 94–99% probability. Describe what your knowledge base actually
contains in the `knowledge` option; the model chooses between meanings, not names.

## Performance

On a 4-core i7-1165G7 laptop with 16 GB RAM and no GPU: about 3–5 seconds per question, one at a time.

## Credits

Model and prompt/decide scripts by [frontier-infra](https://huggingface.co/frontier-infra), downloaded by
`setup.ps1` rather than vendored here. Inference by [llama.cpp](https://github.com/ggml-org/llama.cpp).
