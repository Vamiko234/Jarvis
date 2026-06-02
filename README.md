# Jarvis

A voice + text AI assistant for your PC, powered by a **local** model via
[Ollama](https://ollama.com). Jarvis listens for a wake word, understands your
request, and either answers it or controls your computer by calling **skills**
(open apps, set volume, search files, search the web, take notes, and more).

The model never touches your PC directly — it emits *tool calls*, and a skill
registry executes them. Adding a capability is just writing one decorated function.

```
wake word ─▶ record ─▶ speech-to-text ─▶┐
                                        ├─▶ Brain (Ollama + tools)
typed input ────────────────────────────┘        │
                                                  ├─ tool call? ─▶ skill ─▶ result ─▶ (loop)
                                                  └─ final reply ─▶ speak + print
```

## Quick start (text mode)

1. **Install Ollama** and pull a tool-calling model:
   ```
   ollama pull llama3.1
   ```
2. **Install Jarvis** (core only):
   ```
   pip install -e ".[web,clipboard]"
   ```
3. **Run it:**
   ```
   python -m jarvis.main --text
   ```
   Try: *"what time is it"*, *"take a note: buy milk"*, *"search the web for the
   weather in Tbilisi"*.

## Voice mode (Windows)

Install the voice + Windows extras, then run with `--voice`:
```
pip install -e ".[voice,windows,web,clipboard]"
python -m jarvis.main --voice
```
Say **"Jarvis"**, wait for the prompt, then speak your command.

> On a non-Windows dev machine, system control falls back to a safe **mock**
> adapter (`--adapter mock`) and voice falls back to printing — so you can develop
> and test the brain and skills anywhere.

## Configuration

Everything lives in [`config.yaml`](config.yaml): Ollama host/model, wake word,
STT/TTS engines, which skill groups are enabled, allowed file roots, and which
actions require confirmation (e.g. `shutdown`).

## Skills

| Group            | Examples |
|------------------|----------|
| `system_control` | open/close apps, set/get volume, lock, sleep, shutdown, restart, screenshot, list windows |
| `files`          | search files, read file, open file |
| `web`            | open URL, web search, fetch page text |
| `productivity`   | time, timers, quick notes, clipboard read/write |

Add your own: write a function in `jarvis/skills/`, decorate it with `@skill(...)`.

## Tests

```
pip install -e ".[dev]"
pytest
```
Tests run fully offline using a fake Ollama client and the mock OS adapter.
