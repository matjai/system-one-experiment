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

Needs [uv](https://docs.astral.sh/uv/) and about 6 GB of disk. This creates `.venv`, downloads the llama.cpp CPU
build and the model, and checks the model's SHA-256:

```powershell
.\setup.ps1
```

## Run

Two terminals:

```powershell
.\start-server.ps1                    # llama-server on 127.0.0.1:8080
.venv\Scripts\python.exe app.py       # UI on http://127.0.0.1:5050
```

Or from Python:

```python
from decide import decide

decide("It is raining heavily and I need to walk to the shop.", {
    "bring": {"type": "choice", "instructions": "What should I bring?",
              "criteria": {"umbrella": "keeps you dry in rain", "sunglasses": None, "fan": None}},
})
```

`quick_test.py` runs one example of each question type.

## How it works

`llama-server` knows nothing about decisions. For each question, `decide.py` uses the model repo's own renderer to
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
