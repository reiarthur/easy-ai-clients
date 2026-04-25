# Configuration

`easy-ai-clients` resolves provider credentials from environment variables at
provider-call time. Configure only the credentials for providers your
application actually calls.

`os.environ` is always authoritative. If a variable is already present in the
process, helpers that load local `.env` files preserve that value.

## Recommended Setup

For scripts and applications, load secrets before calling the library:

```python
from dotenv import load_dotenv

load_dotenv()
```

or set variables in the shell:

```bash
export OPENAI_API_KEY="sk-..."
export DEEPGRAM_API_KEY="..."
```

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:DEEPGRAM_API_KEY = "..."
```

Some current text and image helpers attempt to load a `.env` file from the
current working directory before resolving credentials. Audio helpers read the
process environment directly. Because this behavior is not uniform across every
adapter, application code should load `.env` explicitly when it depends on one.

Never commit a real `.env` file. Use the repository template:

[`../.env.example`](../.env.example)

## Recognized Environment Variables

| Variable | Used by |
| --- | --- |
| `ANTHROPIC_API_KEY` | `text.generate(api="anthropic")`, `image.analyze(api="anthropic")` |
| `BFL_API_KEY` | `image.generate / edit / remix(api="bfl")` |
| `COHERE_API_KEY` | `text.generate(api="cohere")` |
| `DEEPGRAM_API_KEY` | `audio.transcribe(api="deepgram")` and OpenAI/Google/Mistral/Together/xAI synthesis alignment paths where used |
| `DEEPGRAM_PROJECT_ID` | Optional Deepgram project filter for catalog/cost lookup calls |
| `DEEPINFRA_API_KEY` | `text.generate(api="deepinfra")`, `audio.generate(api="deepinfra")` |
| `DEEPSEEK_API_KEY` | `text.generate(api="deepseek")` |
| `ELEVENLABS_API_KEY` | `audio.generate(api="elevenlabs")`, `audio.transcribe(api="elevenlabs")` |
| `FAL_KEY` | `text.generate(api="fal")`, `audio.transcribe(api="falai")`, image operations using `api="falai"` |
| `FIREWORKS_API_KEY` | Fireworks text, audio transcription, and image operations |
| `GOOGLE_API_KEY` | Google text, audio generation, and image operations |
| `GROQ_API_KEY` | `text.generate(api="groq")`, `image.analyze(api="groq")` |
| `HUGGINGFACE_API_KEY` | `text.generate(api="huggingface")` |
| `MISTRAL_API_KEY` | `text.generate(api="mistral")`, `audio.generate(api="mistral")` |
| `OPENAI_API_KEY` | OpenAI text, audio, and image operations |
| `OPENROUTER_API_KEY` | OpenRouter operations and some catalog/cost lookup paths |
| `REVAI_API_KEY` | `audio.transcribe(api="revai")` |
| `SPEECHMATICS_API_KEY` | `audio.transcribe(api="speechmatics")` |
| `STABILITY_API_KEY` | `image.generate / edit / remix(api="stability")` |
| `TOGETHER_API_KEY` | Together text, audio, and image operations |
| `XAI_API_KEY` | xAI text, audio, and image operations |

## Missing Credentials

Missing credentials are inert until the corresponding provider is called. For
example, `OPENAI_API_KEY` is not required to call `text.generate(api="anthropic")`.

If a selected provider credential is missing or empty, the call raises a standard
Python exception such as `RuntimeError`, `OSError`, `EnvironmentError`, or
`ValueError`, depending on the adapter path.

## Security Notes

- Keep real tokens out of Git.
- Scope provider tokens to the smallest useful permission set.
- Prefer environment variables supplied by your deployment system in production.
- Avoid printing credentials in logs or exception reports.
- Rotate provider tokens after local testing or incident response.
