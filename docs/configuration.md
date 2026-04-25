# Configuration

`easy-ai-clients` reads provider credentials from environment variables. The
library does **not** auto-load a `.env` file from the package directory or
inject any value implicitly. You can choose how to source secrets in your
own application.

## Recognised environment variables

| Variable | Used by |
| --- | --- |
| `ANTHROPIC_API_KEY` | `text.generate(api="anthropic")`, `image.analyze(api="anthropic")` |
| `BFL_API_KEY` | `image.generate / edit / remix(api="bfl")` |
| `COHERE_API_KEY` | `text.generate(api="cohere")` |
| `DEEPGRAM_API_KEY` | `audio.transcribe(api="deepgram")` |
| `DEEPGRAM_PROJECT_ID` | Optional. Filters Deepgram catalog calls to one project. |
| `DEEPINFRA_API_KEY` | `text.generate(api="deepinfra")`, `audio.generate(api="deepinfra")` |
| `DEEPSEEK_API_KEY` | `text.generate(api="deepseek")` |
| `ELEVENLABS_API_KEY` | `audio.generate(api="elevenlabs")`, `audio.transcribe(api="elevenlabs")` |
| `FAL_KEY` | All `*(api="fal"|"falai")` calls |
| `FIREWORKS_API_KEY` | All `*(api="fireworks")` calls |
| `GOOGLE_API_KEY` | All `*(api="google")` calls |
| `GROQ_API_KEY` | `text.generate(api="groq")`, `image.analyze(api="groq")` |
| `HUGGINGFACE_API_KEY` | `text.generate(api="huggingface")` |
| `MISTRAL_API_KEY` | `text.generate(api="mistral")`, `audio.generate(api="mistral")` |
| `OPENAI_API_KEY` | All `*(api="openai")` calls |
| `OPENROUTER_API_KEY` | All `*(api="openrouter")` calls (also used by `text.generate(api="fal")` for catalog discovery) |
| `REVAI_API_KEY` | `audio.transcribe(api="revai")` |
| `SPEECHMATICS_API_KEY` | `audio.transcribe(api="speechmatics")` |
| `STABILITY_API_KEY` | `image.generate / edit / remix(api="stability")` |
| `TOGETHER_API_KEY` | All `*(api="together")` calls |
| `XAI_API_KEY` | All `*(api="xai")` calls |

The full template lives at [`.env.example`](../.env.example).

## Resolution flow

1. The dispatcher routes the call to the selected provider module.
2. The provider module looks the corresponding variable up in
   `os.environ` only.
3. If the variable is missing or empty, a clear `RuntimeError` /
   `EnvironmentError` is raised before any network request is made.

## Loading a `.env` file explicitly

The simplest way is `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()  # reads `.env` from the current working directory
```

The library will not override variables already set in the current process,
which keeps your shell environment authoritative when you launch the script.

## Shell example

```bash
# bash / zsh
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

python my_script.py
```

```powershell
# PowerShell
$env:OPENAI_API_KEY = "sk-..."
$env:ANTHROPIC_API_KEY = "sk-ant-..."

python my_script.py
```

## Best practices

- Only configure the variables for providers you actually use; missing
  variables are inert until you call that provider.
- Never commit a real `.env` file. Keep `.env` in `.gitignore` (the
  repository's `.gitignore` already does this).
- Use API tokens scoped to the smallest possible set of permissions.
- Rotate tokens regularly and remove them from the environment when running
  unrelated workloads.
