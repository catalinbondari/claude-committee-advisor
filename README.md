# Claude Committee Advisor

A one-page investment committee. Load your holdings by ISIN and weight; nine
AI members, each with one lens, propose trades and rate each other's ideas; a
CIO rules, and every approved trade comes with a new weight, a limit price and
an expiry.

- **Use it:** [Claude Committee Advisor in Claude](https://claude.ai/artifact/HeaRFwvkHcCSH5mLh4kj5r).
  It runs on your own Claude account, so you need to be signed in to Claude.
- **This site:** [catalinbondari.github.io/claude-committee-advisor](https://catalinbondari.github.io/claude-committee-advisor/)
  shows the same page. You can load and check holdings here, but the committee
  itself sits inside Claude: the button takes you there.

## How a sitting works

1. **Holdings.** Upload a CSV, or choose each holding from a list of common
   ETFs and large shares:

   ```
   isin,weight,price
   IE00BK5BQT80,40,138.50
   IE00B5BMR087,20
   US67066G1040,8
   CASH,8
   ```

   Weights are % of the portfolio and add up to 100 with the `CASH` line.
   Price (in euro) is optional and makes the limit price exact. Every ISIN is
   checked against its check digit.
2. **Proposals.** Nine members — the Quant, Reader, US Tech Bull, Income
   Keeper, Moonshot Hunter, Researcher, Goal Keeper, Tax & Cost Officer, and
   Stress Tester — each propose their best buy and weakest holding to sell.
   The CIO then rules on the record.
3. **Peer ratings.** Each member scores the others' ideas from −5 to +5.
4. **CIO ruling.** The CIO approves up to three. House rules then check the
   buys are paid for, the minimum trade, your cap on one company and that no
   sale exceeds a holding. Limits sit 0.8 of the line's usual daily move from
   the last price and are good for 5 trading days.

A sitting makes 19 calls to Claude (9 proposals, 9 ratings, 1 ruling) and
takes about 3 to 6 minutes.

## Privacy

Holdings and the last sitting are kept in your browser only. Nothing is sent
anywhere except to Claude, on your own account, when you convene.

## Try it first

Use **Play demo** for a scripted, offline example; it works on GitHub Pages and
does not use Claude. To inspect the same sample yourself, choose **Load the
sample portfolio** in the page or download
[`samples/sample-portfolio.csv`](samples/sample-portfolio.csv). In the Claude
Artifact, a real sitting runs on the viewer's own Claude account.

## Not advice

The committee recommends; you decide and place any order yourself. Claude
cannot browse, so a price it gives from memory is marked: check the live price
first.

## Editing

Edit `src/page.html` (it is published to Claude as it is), then run
`python3 build.py` to rebuild `index.html` for this site.

An independent tool that runs on Claude; not made or endorsed by Anthropic.
