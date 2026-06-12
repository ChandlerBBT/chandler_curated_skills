# Failure Review And Rule Writeback

## When To Review

Run this playbook after:

- Yellow kill trigger: quick review within 24 hours.
- Orange kill trigger: detailed review within 48 hours.
- Red kill trigger: deep review and rule writeback within 72 hours.
- Any trade where the outcome materially differed from the thesis.

## Failure Types

Common categories:

- False breakout: technical setup looked strong but failed quickly.
- Low-quality earnings beat: headline numbers beat expectations but quality deteriorated.
- Sell-the-news: expected catalyst was already priced in.
- Thesis drift: original reason changed but position remained.
- Positioning error: crowding, leverage, or sentiment overwhelmed fundamentals.
- Regime error: market state did not allow the intended risk.

## Root-Cause Quadrant

Classify primary and secondary cause:

- Analysis error: business, financials, valuation, competition, or risk was misread.
- Execution error: entry, add, stop, trim, or exit plan was not followed.
- Position-sizing error: exposure was too large for confidence, volatility, liquidity, or correlation.
- Regime error: market state made the strategy inappropriate.

Diagnostic order:

1. Was this type of risk allowed by the market regime?
2. If starting fresh today, would the core thesis still be valid?
3. Was the position within the allowed size?
4. Did the entry and exit follow the written plan?

## Review Template

Use this structure:

1. Original thesis: one sentence plus top evidence.
2. Intended action and time horizon.
3. Entry evidence: fundamental, valuation, technical, catalyst, and regime.
4. Ignored counter-evidence.
5. Trigger event.
6. Loss decomposition: market beta, group beta, single-name alpha, sizing, execution cost.
7. Root cause: analysis, execution, sizing, regime.
8. Rule revision.
9. Next action: exit, cooling period, watchlist condition, or renewed thesis requirement.

## Rule Writeback

Every orange or red review must produce at least one rule. A valid rule is:

- Quantified.
- Executable.
- Verifiable.
- Scoped to a market, strategy, setup, or condition.
- Traceable to the review that created it.

Writeback types:

- Add red flag.
- Tighten or loosen threshold.
- Modify position cap.
- Add no-trade condition or cooling period.
- Add a required checklist step.
- Downgrade a hard rule to a warning if opportunity cost is too high.

## Rule Validation

Before making a rule permanent:

1. Back-test conceptually or quantitatively when data exists.
2. Estimate avoided loss versus missed opportunity.
3. Simulate the rule over the next several relevant trades.
4. Promote, revise, or retire the rule.

## Rule Hygiene

- Avoid vague rules like "be careful".
- Avoid rules that cannot be observed in real time.
- Avoid rules that would ban every good opportunity.
- If the same rule triggers repeatedly, review whether the threshold is wrong or the strategy itself is wrong.
