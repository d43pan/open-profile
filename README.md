# Open Profile

Publish your resume and professional identity on your own site, in open formats that people
and their agents can read. This repo is one Agent Skill that **checks** a site and **adds**
what is missing.

It looks for five things:

| # | Piece | Standard |
|---|---|---|
| 1 | Links that say which profiles are you | [`rel="me"`](https://microformats.org/wiki/rel-me) |
| 2 | A description of you | [schema.org `Person`](https://schema.org/Person) in JSON-LD |
| 3 | Your resume as a file | [JSON Resume](https://jsonresume.org/schema) at `/resume.json` |
| 4 | Skills that point at a shared definition | ids from [Wikidata](https://www.wikidata.org) or [ESCO](https://esco.ec.europa.eu) |
| 5 | The same identity in the page's HTML | [h-card](https://microformats.org/wiki/h-card) |

## Check a site

No install needed. Python 3.9+, standard library only:

```
git clone https://github.com/d43pan/open-profile
python3 open-profile/skills/open-profile/scripts/check.py yoursite.com
```

```
5 of 5 for https://mattnicole.com
  ok      rel="me" links to your other profiles: 2 found: ...
  ok      A schema.org Person describing you: Matt Nicole, ...
  ok      Your resume as a file (JSON Resume): Matt Nicole, 12 positions
  ok      Skills that point at a shared definition: 12 ids, ...
  ok      An h-card on the page itself: Matt Nicole
  feeds (not scored): 3
```

Add `--json` for machine-readable output. It reads the page you give it, up to two resume or
about pages that page links to, and `/resume.json`. It stores nothing and sends nothing
anywhere else.

## Use it as a skill

Copy or link `skills/open-profile` into your agent's skills folder. For Claude Code:

```
ln -s "$PWD/open-profile/skills/open-profile" ~/.claude/skills/open-profile
```

Then ask: "check my site's open profile" or "add what's missing". The skill follows
[`references/fixes.md`](skills/open-profile/references/fixes.md), which has the snippet for
each piece and is readable on its own if you'd rather do it by hand.

## Ground rules the skill keeps

- Only your own facts: nothing invented, no taxonomy id written from memory.
- Nothing published that isn't already public. No phone, street address or email unless you ask.
- It reports on any site; it changes only yours, and only when asked.

## Tests

```
python3 -m unittest discover tests
```

MIT licensed.
