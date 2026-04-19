"""Anthropic-style contextual retrieval — chunk-specific context prepended
at index time.

Why: a chunk ripped from its document often loses the context that makes
it findable (company name, date, section heading, entity referent). An
LLM-generated summary of the full doc-relative context, prepended to
each chunk before embedding and BM25 indexing, reduces retrieval failures
by 35-67% in Anthropic's benchmarks.

This module is deliberately tiny: given a (doc, chunks) pair, it returns
contextualized chunks ready to be passed to HybridRetriever.add().

The LLM is called once per chunk (batch-parallelized via ThreadPoolExecutor).
At query time there is zero added cost.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable

# Prompt template from the Anthropic Contextual Retrieval recipe.
_CONTEXTUALIZER_PROMPT = """<document>
{doc}
</document>

Here is a chunk from that document:
<chunk>
{chunk}
</chunk>

Give a short (1-2 sentence) succinct context describing where this chunk
fits in the overall document. The goal is to help a retrieval system find
this chunk on relevant queries. Respond with ONLY the context text, no preamble.
"""


# LLM signature: given a prompt, return the generated text.
LlmFn = Callable[[str], str]


def contextualize_chunks(
    doc: str,
    chunks: list[str],
    llm: LlmFn,
    max_workers: int = 8,
) -> list[str]:
    """Return contextualized chunks: `{ctx}\n\n{chunk}` for each chunk.

    The LLM is called once per chunk in parallel. `llm` is any callable that
    takes a prompt string and returns a string (wrap your OpenAI client).
    """

    def _one(chunk: str) -> str:
        ctx = llm(_CONTEXTUALIZER_PROMPT.format(doc=doc, chunk=chunk)).strip()
        return f"{ctx}\n\n{chunk}" if ctx else chunk

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(_one, chunks))


def make_openai_llm(client, model: str) -> LlmFn:
    """Convenience: wrap an OpenAI-compatible client into the LlmFn signature."""

    def llm(prompt: str) -> str:
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content or ""

    return llm
