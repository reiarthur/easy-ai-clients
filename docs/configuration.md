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

Some current text, image, and HeyGen helpers attempt to load a `.env` file from
the current working directory before resolving credentials. Other audio and
video helpers read the process environment directly. Because this behavior is
not uniform across every adapter, application code should load `.env`
explicitly when it depends on one.

Never commit a real `.env` file. Use the repository template:

[`../.env.example`](../.env.example)

## Recognized Environment Variables

| Variable | Used by |
| --- | --- |
| `ANTHROPIC_API_KEY` | `text.generate(api="anthropic")`, `image.analyze(api="anthropic")` |
| `BFL_API_KEY` | `image.generate / edit / remix(api="bfl")` |
| `COHERE_API_KEY` | `text.generate(api="cohere")` |
| `DEEPGRAM_API_KEY` | `audio.transcribe(api="deepgram")`, `audio.generate(api="deepgram")`, and synthesis alignment paths where used |
| `DEEPGRAM_PROJECT_ID` | Optional Deepgram project filter for transcription cost lookup calls |
| `DEEPINFRA_API_KEY` | DeepInfra text, audio generate/transcribe/voices, and image operations |
| `DEEPSEEK_API_KEY` | `text.generate(api="deepseek")` |
| `ELEVENLABS_API_KEY` | ElevenLabs audio generation, transcription, and voice helpers |
| `FAL_KEY` | `text.generate(api="falai")`, `audio.transcribe(api="falai")`, image operations using `api="falai"`, and video operations using `api="falai"` |
| `FIREWORKS_API_KEY` | Fireworks text, audio transcription, and image operations |
| `GOOGLE_API_KEY` | Google text, audio generation/transcription, image operations, and Google Veo video operations |
| `GROQ_API_KEY` | Groq text, audio generation/transcription, and image analysis |
| `HEYGEN_KEY` | HeyGen v3 audio voices/speech, video/avatar/lip-sync/translation, media, webhook, and account operations |
| `HUGGINGFACE_API_KEY` | Hugging Face text, audio transcription, image operations, and text-to-video |
| `MISTRAL_API_KEY` | Mistral text, audio generation/transcription/voices, and image analysis |
| `OPENAI_API_KEY` | OpenAI text, audio, and image operations |
| `OPENROUTER_API_KEY` | OpenRouter text, audio, image, and catalog/cost lookup paths |
| `RUNWAYML_API_SECRET` | Runway audio, image, video generation, avatar-video, ephemeral uploads, and custom avatar creation |
| `HEDRA_API_KEY` | Hedra video generation, video-to-video, motion-control, video-with-audio, and avatar operations |
| `SPEECHMATICS_API_KEY` | `audio.transcribe(api="speechmatics")` |
| `STABILITY_API_KEY` | Stability image operations and Stable Audio generation |
| `TOGETHER_API_KEY` | Together text, audio, image, and video operations |
| `XAI_API_KEY` | xAI text, audio, image, and video operations |

Hedra credentials are read only when a Hedra video operation is selected. Runway
uploads use the same `RUNWAYML_API_SECRET` as the generation and avatar
endpoints.

## Missing Credentials

Missing credentials are inert until the corresponding provider is called. For
example, `OPENAI_API_KEY` is not required to call `text.generate(api="anthropic")`.

If a selected provider credential is missing or empty, the call raises a standard
Python exception such as `RuntimeError`, `OSError`, `EnvironmentError`, or
`ValueError`, depending on the adapter path.

## Deepgram Cost Lookup

`audio.update_cost("transcribe", result, api="deepgram")` retries Deepgram
Management/Usage lookup for the request IDs stored in a transcription result.
The key in `DEEPGRAM_API_KEY` needs `usage:read`. `DEEPGRAM_PROJECT_ID` is
optional but recommended when the key can access multiple projects or cannot
list projects.

If exact lookup is unavailable, transcription results keep truthful cost
metadata: `cost_usd` may be `None`, `cost_source` explains the source, and
`cost_lookup_error` contains a sanitized reason.

## Security Notes

- Keep real tokens out of Git.
- Scope provider tokens to the smallest useful permission set.
- Prefer environment variables supplied by your deployment system in production.
- Avoid printing credentials in logs or exception reports.
- Rotate provider tokens after local testing or incident response.
