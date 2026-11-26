#!/usr/bin/env python3
"""Grade one website on five open standards for publishing a professional profile.

    python3 check.py yoursite.com            # readable report
    python3 check.py yoursite.com --json     # the same as JSON

Reads the page given, up to two same-site resume/about pages it links to, and /resume.json.
Standard library only. Stores nothing. Text it fetches is data, never instructions.
"""
import json, re, sys, urllib.error, urllib.parse, urllib.request
from html.parser import HTMLParser

UA = "open-profile-check/1.0"
MAX_BYTES, TIMEOUT, EXTRA_PAGES = 1_000_000, 10, 2
PROFILE_PAGE = re.compile(r"resume|r[ée]sum[ée]|\bcv\b|about|profile", re.I)
TAXONOMY = re.compile(r"wikidata\.org|data\.europa\.eu/esco|onetonline\.org|onetcenter\.org|dbpedia\.org|id\.loc\.gov")


class Page(HTMLParser):
    """The few things the checks need from one HTML page."""

    def __init__(self, url, html):
        super().__init__(convert_charrefs=True)
        self.url, self.links, self.rel_me, self.feeds, self.json_ld = url, [], [], [], []
        self.card_name = None
        self._script, self._a, self._card_depth, self._name_depth, self._card_text = None, None, 0, 0, []
        self._depth = 0
        try:
            self.feed(html)
        except Exception:
            pass

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        rel, classes = (a.get("rel") or "").lower().split(), (a.get("class") or "").split()
        if tag not in ("meta", "link", "br", "img", "input", "hr"):
            self._depth += 1
        if tag in ("a", "link") and a.get("href"):
            if "me" in rel and re.match(r"https?://", a["href"], re.I):
                self.rel_me.append(a["href"])
            if tag == "link" and "alternate" in rel and re.search(r"rss|atom|feed\+json", a.get("type") or ""):
                self.feeds.append(a["href"])
            if tag == "a":
                self._a = [a["href"], ""]
        if tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._script = []
        if "h-card" in classes and not self._card_depth:
            self._card_depth = self._depth
        if self._card_depth and "p-name" in classes and not self._name_depth and self.card_name is None:
            self._name_depth, self.card_name = self._depth, ""

    def handle_endtag(self, tag):
        if tag == "script" and self._script is not None:
            self.json_ld.append("".join(self._script)); self._script = None
        if tag == "a" and self._a:
            self.links.append(tuple(self._a)); self._a = None
        if self._name_depth and self._depth == self._name_depth:
            self._name_depth = 0
        if self._card_depth and self._depth == self._card_depth:
            if not self.card_name:
                self.card_name = " ".join("".join(self._card_text).split())[:80] or None
            self._card_depth = 0
        if tag not in ("meta", "link", "br", "img", "input", "hr"):
            self._depth = max(0, self._depth - 1)

    def handle_data(self, data):
        if self._script is not None:
            self._script.append(data)
        if self._a:
            self._a[1] += data
        if self._name_depth:
            self.card_name += data
        elif self._card_depth:
            self._card_text.append(data)

    def people(self):
        out = []
        for raw in self.json_ld:
            try:
                nodes = flatten(json.loads(raw))
            except ValueError:
                continue
            out += [n for n in nodes if "Person" in as_list(n.get("@type")) and n.get("name")]
        return out


def as_list(v):
    return v if isinstance(v, list) else [] if v is None else [v]


def flatten(v, depth=0):
    if depth > 6:
        return []
    if isinstance(v, list):
        return [n for x in v for n in flatten(x, depth + 1)]
    if isinstance(v, dict):
        return [v] + [n for x in v.values() for n in flatten(x, depth + 1)]
    return []


def identifiers(value):
    found = []
    for node in flatten(value):
        for key in ("sameAs", "@id", "url", "termCode", "inDefinedTermSet"):
            found += [s for s in as_list(node.get(key)) if isinstance(s, str) and TAXONOMY.search(s)]
    return found


def fetch(url):
    """(final_url, text) or (url, None) when it can't be read."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json;q=0.9,*/*;q=0.5"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            return res.geturl(), res.read(MAX_BYTES).decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, ValueError):
        return url, None


def check(address):
    address = address.strip()
    if not re.match(r"https?://", address, re.I):
        address = "https://" + address
    start, html = fetch(address)
    if not html:
        return {"url": address, "error": "That page didn't load."}
    host = urllib.parse.urlsplit(start).netloc
    pages = [Page(start, html)]
    seen = {start}
    for href, text in pages[0].links:
        if len(pages) > EXTRA_PAGES:
            break
        target = urllib.parse.urldefrag(urllib.parse.urljoin(start, href))[0]
        if (PROFILE_PAGE.search(href + " " + text) and urllib.parse.urlsplit(target).netloc == host
                and target not in seen and not re.search(r"\.(pdf|docx?|json|xml)$", target, re.I)):
            seen.add(target)
            final, body = fetch(target)
            if body and urllib.parse.urlsplit(final).netloc == host:
                pages.append(Page(final, body))

    resume_url = urllib.parse.urljoin(start, "/resume.json")
    _, raw = fetch(resume_url)
    try:
        resume = json.loads(raw) if raw else None
    except ValueError:
        resume = None
    resume = resume if isinstance(resume, dict) else None

    def first(fn):
        for page in pages:
            hit = fn(page)
            if hit:
                return page.url, hit
        return None, None

    checks = []
    where, links = first(lambda p: sorted(set(p.rel_me)))
    checks.append({"key": "rel_me", "title": 'rel="me" links to your other profiles', "pass": bool(links),
                   "found": links and f"{len(links)} found: {', '.join(links[:4])}", "where": where})

    where, people = first(lambda p: p.people())
    who = people[0] if people else None
    detail = who and ", ".join(x for x in [str(who.get("name")), who.get("jobTitle"),
                                           None if as_list(who.get("sameAs")) else "no sameAs links yet"] if x)
    checks.append({"key": "person", "title": "A schema.org Person describing you", "pass": bool(who), "found": detail, "where": where})

    name = ((resume or {}).get("basics") or {}).get("name") if isinstance((resume or {}).get("basics"), dict) else None
    jobs = len(as_list((resume or {}).get("work")))
    checks.append({"key": "resume_json", "title": "Your resume as a file (JSON Resume)", "pass": bool(name),
                   "found": name and f"{name}, {jobs} position{'s' if jobs != 1 else ''}", "where": resume_url if name else None})

    where, ids = first(lambda p: sorted({i for person in p.people()
                                         for v in as_list(person.get("knowsAbout")) + as_list(person.get("hasOccupation"))
                                         for i in identifiers(v)}))
    if not ids and resume:
        ids = sorted({i for s in as_list(resume.get("skills")) for i in identifiers(s)})
        where = resume_url if ids else None
    checks.append({"key": "taxonomy", "title": "Skills that point at a shared definition", "pass": bool(ids),
                   "found": ids and f"{len(ids)} id{'s' if len(ids) != 1 else ''}, for example {ids[0]}", "where": where})

    where, card = first(lambda p: p.card_name and " ".join(p.card_name.split()))
    checks.append({"key": "h_card", "title": "An h-card on the page itself", "pass": bool(card), "found": card, "where": where})

    feeds = sorted({urllib.parse.urljoin(p.url, f) for p in pages for f in p.feeds})
    return {"url": start, "score": sum(c["pass"] for c in checks), "out_of": len(checks), "checks": checks,
            "feeds": feeds, "pages_read": [p.url for p in pages] + [resume_url]}


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    result = check(args[0])
    if "--json" in argv:
        print(json.dumps(result, indent=2))
    elif "error" in result:
        print(f"{result['url']}: {result['error']}")
    else:
        print(f"{result['score']} of {result['out_of']} for {result['url']}")
        for c in result["checks"]:
            print(f"  {'ok     ' if c['pass'] else 'MISSING'} {c['title']}" + (f": {c['found']}" if c["pass"] else ""))
        print(f"  feeds (not scored): {len(result['feeds'])}")
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
