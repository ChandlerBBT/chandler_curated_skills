# stock_analysis

`stock-analysis` is a Codex skill for disciplined stock research. Its human-facing display name is `stock_analysis`.

It helps Codex run a reusable investment research process covering:

- mandate intake and market-regime control
- candidate screening
- fundamentals and financial-statement quality
- valuation method selection and scenario discipline
- technical timing frameworks such as stage analysis, SEPA/VCP, CANSLIM-style checklists, relative strength, and volume/price confirmation
- catalyst and policy validation
- position sizing and kill criteria
- failure review and rule writeback

## What It Avoids

This skill intentionally does not bind itself to a note app, chart-delivery workflow, web page generator, or external task artifact system. It defaults to research reasoning and investment judgment in chat.

It also does not include concrete company, ticker, or industry case studies. Those should come from the user request or verified sources during the actual research task.

## Example Prompts

```text
Use $stock-analysis to evaluate whether this stock deserves a trial position, standard position, watchlist status, or pass.
```

```text
Use $stock-analysis to review this earnings release: separate headline beat from financial-quality beat, then update thesis and kill criteria.
```

```text
Use $stock-analysis to build a valuation view with method selection, base/bull/bear assumptions, sensitivity, and missing-data labels.
```

```text
Use $stock-analysis to review a failed trade and write back one quantified rule.
```

## Install

Install from:

```text
https://github.com/ChandlerBBT/chandler_curated_skills/tree/main/skills/stock-analysis
```

Restart Codex after installation so the skill can be loaded.
