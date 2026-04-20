# Example 03 — Financial: recent NVDA earnings commentary

Domain: `financial` · Expected wall-clock on Mac M4 Pro: ~60-80 s.

## The question

> Summarize the last two quarters of NVIDIA (NVDA) reported revenue,
> data-center segment growth, and management commentary on AI-training
> demand. Cite SEC filings or official earnings calls where possible.

## Command

```bash
make cli Q="Summarize the last two quarters of NVIDIA (NVDA) reported revenue, data-center segment growth, and management commentary on AI-training demand. Cite SEC filings or official earnings calls where possible." --domain financial
```

## What the `financial` preset contributes

- **seed_queries** include `site:sec.gov`, `10-K annual report`, `10-Q quarterly report`, `earnings call transcript` — primary-source bias.
- **searxng_categories: [news]** — recent-news weighting.
- **min_verified_ratio: 0.80** — stricter than medical because financial misinformation is high-risk.
- **prompt_extra** requires explicit date stamps on every numeric claim ("FY2025 Q4 per 10-K filed 2026-02-14") and disclaims forward-looking predictions.

## Expected output shape

```
Q: Summarize the last two quarters of NVIDIA (NVDA) reported revenue,
   data-center segment growth, and management commentary on AI-training
   demand. Cite SEC filings or official earnings calls where possible.

[class: synthesis]

A: NVIDIA's two most recent reported quarters (FY2026 Q4, reported
   2026-02-21, and FY2026 Q3, reported 2025-11-15):

   **Revenue (total):**
     - FY2026 Q4: [revenue figure] [1]
     - FY2026 Q3: [revenue figure] [1][2]
     All figures per the SEC 10-Q filings cited.

   **Data-center segment:**
     - FY2026 Q4: [data-center revenue] (segment growth +X% YoY) [1]
     - FY2026 Q3: [data-center revenue] (segment growth +X% YoY) [1]

   **Management commentary on AI-training demand:**
     - [CEO/CFO quote from earnings call] [3]
     - [Forward-looking disclosure per Regulation FD] [4]

   This is research, not investment advice. All figures are audited
   reported numbers, not analyst estimates or management guidance.

Cited sources:
  [1] ● https://www.sec.gov/ix?doc=/Archives/edgar/data/1045810/…/nvda-10q-q4.htm
        NVDA 10-Q, FY2026 Q4, filed 2026-02-21
  [2] ● https://www.sec.gov/…/nvda-10q-q3.htm
        NVDA 10-Q, FY2026 Q3, filed 2025-11-15
  [3] ● https://investor.nvidia.com/financial-info/quarterly-results/…
        Q4 earnings call transcript
  [4] ● https://reuters.com/…

Hallucination check — 6/6 claims verified
  ✓ FY2026 Q4 revenue figure matches filed 10-Q
  ✓ FY2026 Q3 revenue figure matches filed 10-Q
  ✓ Data-center segment growth figures match segment reporting
  ✓ CEO commentary matches earnings call transcript
  ✓ Forward-looking disclosure flagged as such
  ✓ All figures have an explicit reporting date

Trace (per-node totals):
  search      26.1 s  (SearXNG biased to SEC + Reuters + Bloomberg)
  fetch_url   18.7 s  (10-Q HTML is heavy; trafilatura extracts text)
  compress     9.1 s  (collapses SEC filings to claim-level)
  synthesize   6.2 s
  verify       8.3 s  (stricter than default — financial preset)
  plan         4.8 s
  classify     2.9 s
  retrieve     0.9 s

  total: 77.0 s · ~16800 tokens · iterations=1
```

## Why the trade-off is honest

- Numeric accuracy on 10-Q extractions requires trafilatura to successfully parse the SEC's inline-XBRL HTML. Occasionally this fails on legacy filings; in those cases the pipeline surfaces a snippet-based approximation and CoVe flags it (`✗ FY-X Q-Y revenue: could not verify from extracted text`).
- Forward-looking claims (guidance, analyst targets) are NEVER asserted as fact. The prompt_extra enforces this.
- The preset does not connect to live market-data APIs. For real-time prices, layer the `stock_trading` preset's `yfinance` tooling separately (or use the trading-copilot recipe).

## Safety

The `financial` preset contains no buy/sell/hold recommendation logic. See `stock_trading.yaml` for the preset that explicitly **refuses** such recommendations — even if the user asks directly.
