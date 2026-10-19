# deepgram-keyterms

Deepgram-keyterms: how much of Nova-3's rare-word gain can keyterms pulled automatically from a
company's own 10-K recover, measured against Rev's oracle list?

Data: Rev's Earnings-21, the 10-call eval subset. Each call gets transcribed three ways: no keyterms,
keyterms extracted automatically from the company's SEC 10-K, and oracle keyterms (terms from Rev's
published oracle_list.txt that actually occur in that call). The metric is recall of oracle-list terms,
the rare-word metric Rev used in its own contextual biasing paper.

## Results

<!-- results:start -->
# Nova-3 keyterms on Earnings-21, 2026-10-19

10 calls, 990 occurrences of Rev oracle-list terms. Recall of those terms in Nova-3's transcript:

| Keyterms | Rare-word recall |
|---|---|
| None | 0.797 |
| Auto, from each company's 10-K | 0.818 |
| Oracle, Rev's list | 0.819 |

**Automatic keyterms recovered 95% of the oracle's gain.**

| Call | Company | 10-K used | Keyterms sent, auto / oracle | none | auto | oracle |
|---|---|---|---|---|---|---|
| 4320211 | Monro Inc | MONRO, INC. 10-K filed 2021-05-26 | 100 / 32 | 0.658 | 0.904 | 0.753 |
| 4341191 | General Electric | GENERAL ELECTRIC CO 10-K filed 2021-02-12 | 50 / 56 | 0.859 | 0.852 | 0.873 |
| 4346818 | Ingersoll Rand | Ingersoll Rand Inc. 10-K filed 2021-02-26 | 50 / 54 | 0.801 | 0.809 | 0.809 |
| 4359971 | Constellium | CONSTELLIUM SE 20-F filed 2021-03-17 | 100 / 41 | 0.726 | 0.726 | 0.761 |
| 4365024 | Nextar Media Group | NEXSTAR MEDIA GROUP, INC. 10-K filed 2021-03-01 | 100 / 53 | 0.882 | 0.899 | 0.908 |
| 4366522 | Aldeyra Therapeutics Inc | Aldeyra Therapeutics, Inc. 10-K filed 2021-03-11 | 100 / 21 | 0.688 | 0.688 | 0.625 |
| 4366893 | Earthstone Energy Inc | EARTHSTONE ENERGY INC 10-K filed 2021-03-10 | 100 / 27 | 0.766 | 0.750 | 0.797 |
| 4367535 | Affimed | Affimed N.V. 20-F filed 2021-04-15 | 100 / 29 | 0.780 | 0.802 | 0.846 |
| 4383161 | Pilgrims Pride Corp | PILGRIMS PRIDE CORP 10-K filed 2021-02-11 | 50 / 42 | 0.787 | 0.798 | 0.777 |
| 4384964 | Eversource | EVERSOURCE ENERGY 10-K filed 2021-02-17 | 50 / 58 | 0.849 | 0.841 | 0.849 |

## Honest limits

- Recall counts term occurrences in the reference and the transcript, capped per term. It doesn't align words, so a term transcribed in the wrong place still counts.
- The oracle list comes from the reference transcripts themselves, so it's an upper bound no real deployment gets.
- The 10-K used is the latest one filed by mid-2021, close to when these calls happened. Ten calls; per-call numbers vary a lot.
## Where the gain came from

Most of the overall gain comes from Monro. Its own strategic plan, Monro Forward, appears 14 times in the call. Nova-3 got it right once without keyterms and wrote Monroe five times. With keyterms from Monro's 10-K, it got all 14 right. Names that collide with common words are where automatic keyterms pay off.

<!-- results:end -->

## Run it

```
pip install -r requirements.txt
cp .env.example .env    # keys: DEEPGRAM_API_KEY, SEC_USER_AGENT
python bench.py
```

Every run writes `results/<date>.md` with the numbers and an honest-limits section.

## License

MIT
