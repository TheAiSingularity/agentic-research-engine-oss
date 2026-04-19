# youtube-analyzer

**Levels:** beginner ⬛ · production ⬛ · rust ⬛ · **all pending — ships in Wave 1**

## What it does
Given a YouTube URL, produces:
- Transcript (via `yt-dlp` — no YouTube API key required)
- Chapter breakdown with timestamps
- Summary
- Suggested alternative titles
- Key-quote extraction

## Who it's for
- Content creators researching topics and auditing their own videos
- Teams summarizing long-form talks, podcasts, or lectures
- Anyone who wants a structured-output agent example

## Why you'd use it
- No API keys to start — `yt-dlp` is enough for transcripts
- Shows a pipeline-style agent (fetch → transcribe → analyze → summarize → structure)
- Great showcase for typed outputs (chapter schema, title-suggestion schema)

## Framework implementations (Wave 1)

| Variant | Why this framework |
|---|---|
| [`beginner/vanilla/`](beginner/vanilla/) | Baseline — straight pipeline with tool-calling |
| [`beginner/langgraph/`](beginner/langgraph/) | Stateful pipeline with retry branches |
| [`beginner/crewai/`](beginner/crewai/) | Multi-agent — transcriber + summarizer + editor crew |
| [`beginner/pydantic-ai/`](beginner/pydantic-ai/) | Typed outputs — structured chapter and title schemas are Pydantic AI's sweet spot |

## See also
- [`comparison.md`](comparison.md) — benchmark table across the four implementations (lands Wave 1)
