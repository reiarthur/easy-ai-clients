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
| `BEATOVEN_API_KEY` | `music.text_to_music(api="beatoven")`, `music.stem_separation(api="beatoven")` |
| `BFL_API_KEY` | `image.generate / edit / remix(api="bfl")` |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Workers AI endpoint routing for `music.*(api="cloudflare")` |
| `CLOUDFLARE_API_TOKEN` | Cloudflare music operations using `api="cloudflare"` |
| `COHERE_API_KEY` | `text.generate(api="cohere")` |
| `DEAPI_API_KEY` | DeAPI music operations |
| `DEEPGRAM_API_KEY` | `audio.transcribe(api="deepgram")`, `audio.generate(api="deepgram")`, and synthesis alignment paths where used |
| `DEEPGRAM_PROJECT_ID` | Optional Deepgram project filter for transcription cost lookup calls |
| `DEEPINFRA_API_KEY` | DeepInfra text, audio generate/transcribe/voices, and image operations |
| `DEEPSEEK_API_KEY` | `text.generate(api="deepseek")` |
| `ELEVENLABS_API_KEY` | ElevenLabs audio generation, transcription, voice helpers, and music operations |
| `FAL_KEY` | `text.generate(api="falai")`, `audio.transcribe(api="falai")`, image operations using `api="falai"`, video operations using `api="falai"`, and music operations using `api="falai"` |
| `FIREWORKS_API_KEY` | Fireworks text, audio transcription, and image operations |
| `GENERATESONGS_API_KEY` | GenerateSongs music operations |
| `GOOGLE_API_KEY` | Google text, audio generation/transcription, image operations, Google Veo video operations, and Google music operations |
| `GROQ_API_KEY` | Groq text, audio generation/transcription, and image analysis |
| `HEYGEN_KEY` | HeyGen v3 audio voices/speech, video/avatar/lip-sync/translation, media, webhook, and account operations |
| `HUGGINGFACE_API_KEY` | Hugging Face text, audio transcription, image operations, and text-to-video |
| `JEN_MUSIC_API_KEY` | Jen music operations |
| `MINIMAX_API_KEY` | MiniMax music operations |
| `MISTRAL_API_KEY` | Mistral text, audio generation/transcription/voices, and image analysis |
| `MODELSLAB_API_KEY` | ModelsLab music operations |
| `MUSICFUL_API_KEY` | Musicful music operations |
| `MUSICFY_API_KEY` | Musicfy music operations |
| `MUSICGPT_API_KEY` | MusicGPT music operations |
| `NOVITA_API_KEY` | Novita music operations |
| `OPENAI_API_KEY` | OpenAI text, audio, and image operations |
| `OPENROUTER_API_KEY` | OpenRouter text, audio, image, and catalog/cost lookup paths |
| `REPLICATE_API_TOKEN` | Replicate music operations |
| `RUNWARE_API_KEY` | Runware music operations |
| `RUNWAYML_API_SECRET` | Runway audio, image, video generation, avatar-video, ephemeral uploads, and custom avatar creation |
| `SCENARIO_API_KEY` | Scenario music operations |
| `SCENARIO_API_SECRET` | Scenario music operations |
| `SEGMIND_API_KEY` | Segmind music operations |
| `HEDRA_API_KEY` | Hedra video generation, video-to-video, motion-control, video-with-audio, and avatar operations |
| `SPEECHMATICS_API_KEY` | `audio.transcribe(api="speechmatics")` |
| `SONAUTO_API_KEY` | Sonauto music operations |
| `SOUNDVERSE_API_KEY` | Soundverse music operations |
| `STABILITY_API_KEY` | Stability image operations, Stable Audio generation, and music operations |
| `TOPMEDIAI_API_KEY` | TopMediai music operations |
| `TOGETHER_API_KEY` | Together text, audio, image, and video operations |
| `WAVESPEEDAI_API_KEY` | WaveSpeedAI music operations |
| `XAI_API_KEY` | xAI text, audio, image, and video operations |

Hedra credentials are read only when a Hedra video operation is selected. Runway
uploads use the same `RUNWAYML_API_SECRET` as the generation and avatar
endpoints.

Music provider credentials are also read at provider-call time. Importing
`easy_ai_clients.music` does not require credentials.

Do not pass API keys or tokens as public music operation kwargs. The dispatcher
rejects credential-like kwargs such as `api_key`, `token`, and `authorization`.

Direct music URL downloads require `output_path`:

```python
from easy_ai_clients import music

result = music.download(
    "text_to_music",
    audio_url="https://example.com/song.mp3",
    output_path="song.mp3",
    api="google",
)
```

The wrapper does not save files implicitly.

## Live Music Tests

Normal tests do not call music provider APIs.

The gated live music test module is skipped unless:

```text
EASY_AI_CLIENTS_LIVE_MUSIC=1
```

Paid live smoke calls also require:

```text
EASY_AI_CLIENTS_LIVE_MUSIC_PAID_CALL=1
```

Do not enable these variables for normal package validation.

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
