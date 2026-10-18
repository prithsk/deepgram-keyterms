"""deepgram-keyterms: how much of Nova-3's rare-word gain can keyterms pulled automatically from a
company's own 10-K recover, measured against Rev's oracle list?

Data: Rev's Earnings-21, the 10-call eval subset. Each call gets transcribed three ways: no keyterms,
keyterms extracted automatically from the company's SEC 10-K, and oracle keyterms (terms from Rev's
published oracle_list.txt that actually occur in that call). The metric is recall of oracle-list terms,
the rare-word metric Rev used in its own contextual biasing paper.

  python bench.py            # needs DEEPGRAM_API_KEY and SEC_USER_AGENT in .env
"""
import argparse, collections, csv, html, io, json, re, statistics, time, urllib.parse, urllib.request, datetime as dt
from common import ROOT, need, os

RAW = "https://raw.githubusercontent.com/revdotcom/speech-datasets/main/earnings21/"
STOP = set("""the a an and or of to in for on with by at from as is are be this that these those our we us its it their
company companies inc incorporated corp corporation co llc ltd plc group holdings form item part annual report securities exchange
commission sec united states federal state january february march april may june july august september october november december
fiscal year quarter total net income revenue operating financial statements notes table contents page however including
management board directors officer chief executive president vice see also during under other such may would could""".split())

def fetch(url, binary=False, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "deepgram-keyterms"})
    data = urllib.request.urlopen(req, timeout=120).read(); return data if binary else data.decode("utf-8", "replace")

def files():
    rows = list(csv.DictReader(io.StringIO(fetch(RAW + "eval10-file-metadata.csv"))))
    return [(r["file_id"], r["company_name"]) for r in rows]

def reference(fid):
    lines = fetch(RAW + f"transcripts/nlp_references/{fid}.nlp").splitlines()[1:]
    return " ".join(l.split("|")[0] for l in lines if l.strip())

def count(term, text):
    return len(re.findall(r"(?<![A-Za-z0-9])" + re.escape(term.lower()) + r"(?![A-Za-z0-9])", text.lower()))

def oracle_terms(ref, oracle_list, cap=100):
    present = [t for t in oracle_list if count(t, ref)]
    return sorted(present, key=lambda t: (-len(t.split()), -count(t, ref)))[:cap]

def extract_terms(doc_text, cap=100):
    """Rare-word candidates from a filing: capitalized phrases and acronyms the document itself treats as names."""
    text = re.sub(r"\s+", " ", doc_text)
    lower_counts = collections.Counter(w for w in re.findall(r"\b[a-z][a-z'-]+\b", text))
    cands = collections.Counter()
    for m in re.finditer(r"\b(?:[A-Z][a-zA-Z&'-]+)(?:\s+[A-Z][a-zA-Z&'-]+){0,3}\b", text):
        words = m.group(0).split()
        while words and words[0].lower() in STOP: words = words[1:]
        while words and words[-1].lower() in STOP: words = words[:-1]
        if not words: continue
        phrase = " ".join(words)
        if len(words) == 1 and (lower_counts[phrase.lower()] > 2 or len(phrase) < 3): continue   # common word, just capitalized
        if all(w.lower() in STOP for w in words): continue
        cands[phrase] += 1
    for a in re.findall(r"\b[A-Z]{2,6}\b", text):
        if a.lower() not in STOP: cands[a] += 1
    return [t for t, n in cands.most_common(cap * 3) if n >= 2][:cap]

def ten_k_text(company, ua, before="2021-06-30"):
    h = {"User-Agent": ua}
    tickers = json.loads(fetch("https://www.sec.gov/files/company_tickers.json", headers=h))
    want = set(re.findall(r"[a-z]+", company.lower())) - {"inc", "corp", "corporation", "co", "the", "company"}
    best = max(tickers.values(), key=lambda t: len(want & set(re.findall(r"[a-z]+", t["title"].lower()))) / max(1, len(want)))
    sub = json.loads(fetch(f"https://data.sec.gov/submissions/CIK{int(best['cik_str']):010d}.json", headers=h))
    r = sub["filings"]["recent"]
    ks = [(r["filingDate"][i], r["accessionNumber"][i], r["primaryDocument"][i]) for i, f in enumerate(r["form"]) if f == "10-K"]
    if not ks: return best["title"], ""
    early = [k for k in ks if k[0] <= before]; d, acc, doc = (max(early) if early else min(ks))
    url = f"https://www.sec.gov/Archives/edgar/data/{int(best['cik_str'])}/{acc.replace('-', '')}/{doc}"
    time.sleep(0.2)
    raw = fetch(url, headers=h); text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return f"{best['title']} 10-K filed {d}", text

def transcribe(audio, keyterms):
    q = [("model", "nova-3"), ("punctuate", "true")] + [("keyterm", t) for t in keyterms]
    req = urllib.request.Request("https://api.deepgram.com/v1/listen?" + urllib.parse.urlencode(q), data=audio, method="POST",
                                 headers={"Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}", "Content-Type": "audio/mpeg"})
    j = json.loads(urllib.request.urlopen(req, timeout=900).read())
    return j["results"]["channels"][0]["alternatives"][0]["transcript"]

def term_recall(terms, ref, hyp):
    tot = hit = 0
    for t in terms:
        r = count(t, ref)
        if r: tot += r; hit += min(r, count(t, hyp))
    return hit / tot if tot else float("nan"), tot

def main(limit):
    need("DEEPGRAM_API_KEY", "SEC_USER_AGENT")
    oracle_list = [l.strip() for l in fetch(RAW + "bias_lists/oracle_list.txt").splitlines() if l.strip()]
    cache = ROOT / "cache"; cache.mkdir(exist_ok=True); rows = []
    for fid, company in files()[:limit]:
        ref = reference(fid); evalset = [t for t in oracle_list if count(t, ref)]
        src, doc = ten_k_text(company, os.environ["SEC_USER_AGENT"]); auto = extract_terms(doc)
        conds = {"none": [], "auto_10k": auto, "oracle": oracle_terms(ref, oracle_list)}
        audio = None; res = {"file": fid, "company": company, "source": src, "eval_terms": len(evalset), "auto_terms": len(auto)}
        for name, kt in conds.items():
            cf = cache / f"{fid}-{name}.txt"
            if not cf.exists():
                audio = audio or fetch(RAW + f"media/{fid}.mp3", binary=True)
                cf.write_text(transcribe(audio, kt), encoding="utf-8"); print(f"  {company} {name}: transcribed", flush=True)
            res[name], res["n_occ"] = term_recall(evalset, ref, cf.read_text(encoding="utf-8"))
        res["auto_overlap"] = len({t.lower() for t in auto} & {t.lower() for t in evalset})
        rows.append(res); print(f"  {company}: none {res['none']:.3f} | auto {res['auto_10k']:.3f} | oracle {res['oracle']:.3f}", flush=True)
    occ = sum(r["n_occ"] for r in rows)
    agg = {k: sum(r[k] * r["n_occ"] for r in rows) / occ for k in ("none", "auto_10k", "oracle")}
    recov = (agg["auto_10k"] - agg["none"]) / (agg["oracle"] - agg["none"]) if agg["oracle"] > agg["none"] else float("nan")
    md = [f"# Nova-3 keyterms on Earnings-21, {dt.date.today()}", "",
          f"{len(rows)} calls, {occ} occurrences of Rev oracle-list terms. Recall of those terms in Nova-3's transcript:", "",
          "| Keyterms | Rare-word recall |", "|---|---|",
          f"| None | {agg['none']:.3f} |", f"| Auto, from each company's 10-K | {agg['auto_10k']:.3f} |", f"| Oracle, Rev's list | {agg['oracle']:.3f} |", "",
          f"**Automatic keyterms recovered {100 * recov:.0f}% of the oracle's gain.**", "",
          "| Call | Company | 10-K used | none | auto | oracle |", "|---|---|---|---|---|---|"]
    md += [f"| {r['file']} | {r['company']} | {r['source']} | {r['none']:.3f} | {r['auto_10k']:.3f} | {r['oracle']:.3f} |" for r in rows]
    md += ["", "## Honest limits", "",
           "- Recall counts term occurrences in the reference and the transcript, capped per term. It doesn't align words, so a term transcribed in the wrong place still counts.",
           "- The oracle list comes from the reference transcripts themselves, so it's an upper bound no real deployment gets.",
           "- The 10-K used is the latest one filed by mid-2021, close to when these calls happened. Ten calls; per-call numbers vary a lot."]
    (ROOT / "results").mkdir(exist_ok=True); out = "\n".join(md); (ROOT / "results" / f"{dt.date.today()}.md").write_text(out, encoding="utf-8"); print(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int, default=10); main(ap.parse_args().limit)
