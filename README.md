# Jarvis

A voice + text AI assistant for your Windows PC, powered by **local models via
[Ollama](https://ollama.com)** — no API keys, no cloud, no monthly cost.

Tell it to open Amazon and order something. Ask it to research a topic and get a
cited report. Control your PC by voice. Everything runs on your own hardware.

```
voice ("Jarvis…") ──▶ STT ──▶┐
                              ├──▶ Brain (Ollama + tools) ──▶ skill dispatch ──▶ PC / browser / web
typed command ────────────────┘
```

---

## Requirements

- **Windows 10/11** (voice + desktop control); core runs on Linux/Mac too
- **Python 3.11+** — https://www.python.org/downloads/ (check "Add to PATH")
- **Ollama** — https://ollama.com/download
- **RTX GPU recommended** for 32B model; 7B runs fine on CPU

---

## Quick start

### 1. Clone and set up

```bat
git clone https://github.com/Vamiko234/Jarvis
cd Jarvis
setup_windows.bat
```

The script installs all dependencies, pulls the three Ollama models (~29 GB
total), and installs Playwright's Chromium browser. Run it once.

### 2. Start Ollama

Ollama runs as a background server. Either launch the Ollama desktop app, or:

```bat
ollama serve
```

### 3. Run Jarvis

**Browser UI** (recommended — see task tracker, confirm actions in-browser):
```bat
python -m jarvis.main --ui
```
Open **http://127.0.0.1:8765** in your browser.

**Text mode** (terminal only, no browser needed):
```bat
python -m jarvis.main --text
```

**Voice mode** (say "Jarvis" to activate):
```bat
python -m jarvis.main --voice
```

---

## What it can do

### Simple commands
- *"What time is it"* / *"Set a 10-minute timer"*
- *"Take a note: buy milk"* / *"Read my notes"*
- *"Copy this to clipboard: meeting at 3pm"*
- *"Search the web for Python asyncio tutorial"*

### System control (Windows)
- *"Open Chrome"* / *"Close Spotify"*
- *"Set volume to 40"* / *"Take a screenshot"*
- *"Lock the screen"* / *"Sleep the PC"* / *"Restart"* (asks confirmation)

### Browser tasks (Playwright)
- *"Go to Amazon and search for a mechanical keyboard under $100, add the top result to my cart"*
- *"Log into Gmail and read my latest 3 emails"*
- *"Fill out the contact form on [site] with my info"*

Jarvis **pauses and asks your confirmation** before clicking any checkout,
payment, or submit button.

### Research
- *"Research the best budget GPUs for gaming in 2025"*

Decomposes your question, searches multiple sources, fetches pages, and
synthesizes a cited markdown report saved to `~/.jarvis/research/`.

### Desktop vision (experimental)
- *"Open Spotify and play my liked songs"*
- *"Click the minimize button on the current window"*

Uses your vision model to look at a screenshot and click/type. Less reliable
than browser automation — use browser tasks for anything web-based.

---

## Models

Three tiers, automatically selected per request:

| Tier    | Model            | Used for                                  |
|---------|------------------|-------------------------------------------|
| `fast`  | `qwen2.5:7b`     | Simple Q&A, system commands, notes, time  |
| `smart` | `qwen2.5:32b`    | Browser tasks, research, multi-step plans |
| `vision`| `qwen2.5-vl:7b`  | Desktop screenshot + click control        |

The tier badge in the UI (`7B` / `32B` / `VL`) updates as you type, showing
which model will handle your request.

Change models in `config.yaml` under the `models:` section.

---

## Configuration

All settings live in [`config.yaml`](config.yaml). Key options:

```yaml
brain:
  host: "http://localhost:11434"   # Ollama server address
  max_tool_iterations: 8           # max tool calls per response

models:
  fast:   "qwen2.5:7b"
  smart:  "qwen2.5:32b"
  vision: "qwen2.5-vl:7b"

browser:
  headless: false                  # false = visible browser window
  profile_dir: "~/.jarvis/browser_profile"  # saved logins live here

agents:
  autonomy: "pause_before_commit"  # pause_before_commit | never_commit | full

safety:
  confirm_actions: [shutdown, restart, delete_file]
  blocked_actions: []              # completely prevent these skills
```

---

## Adding skills

Drop a file in `jarvis/skills/`, decorate a function with `@skill`:

```python
from jarvis.skills import skill

@skill(
    name="weather",
    description="Get current weather for a city.",
    parameters={"city": {"type": "string", "description": "City name"}},
)
def weather(city: str) -> str:
    # ...fetch weather API...
    return f"It's 72°F and sunny in {city}."
```

The registry auto-generates the Ollama tool schema. No other wiring needed.

---

## Running tests

```bat
pip install pytest
pytest
```

Tests run fully offline using a fake Ollama client and a mock OS adapter —
no Ollama install needed to run the test suite.

---

## Troubleshooting

**"Can't reach Ollama"** — Run `ollama serve` in a separate terminal, or launch
the Ollama desktop app. Then verify with `ollama list`.

**Browser tasks don't open a window** — Set `browser.headless: false` in
`config.yaml`. Also run `playwright install chromium` if you skipped setup.

**Voice mode not working** — Voice dependencies (`sounddevice`, `faster-whisper`,
`openwakeword`, `pyttsx3`) must be installed: `pip install sounddevice numpy
faster-whisper openwakeword pyttsx3`.

**32B model is slow** — It loads on first use (~20s on an RTX 4080). Subsequent
requests are fast. Set `models.keep_alive: "10m"` in config to keep it resident
longer.
