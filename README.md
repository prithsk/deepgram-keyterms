# deepgram-keyterms

Deepgram-keyterms: how much of Nova-3's rare-word gain can keyterms pulled automatically from a
company's own 10-K recover, measured against Rev's oracle list?

Data: Rev's Earnings-21, the 10-call eval subset. Each call gets transcribed three ways: no keyterms,
keyterms extracted automatically from the company's SEC 10-K, and oracle keyterms (terms from Rev's
published oracle_list.txt that actually occur in that call). The metric is recall of oracle-list terms,
the rare-word metric Rev used in its own contextual biasing paper.

## Results

<!-- results:start -->
_Run it to populate._
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
