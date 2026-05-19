# audio.generate(api="groq")

Groq text-to-speech using the OpenAI-compatible audio speech endpoint.

Environment variable: `GROQ_API_KEY`

Default model: `playai-tts`

The wrapper returns `cost_usd=None/0` style metadata as unavailable when the
provider does not return usage or a deterministic public USD table.

