"""Offline tests: the checks run against canned pages, no network."""
import importlib.util, json, pathlib, unittest

spec = importlib.util.spec_from_file_location(
    "check", pathlib.Path(__file__).parent.parent / "skills" / "open-profile" / "scripts" / "check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

HOME = """<html><head><link rel="me" href="https://github.com/someone">
<link rel="alternate" type="application/rss+xml" href="/feed.xml"></head>
<body><a href="/resume">My resume</a> <a href="/resume.pdf">PDF</a>
<a href="https://other.example/about">Elsewhere</a></body></html>"""
RESUME = """<html><head><script type="application/ld+json">
{"@context":"https://schema.org","@type":"ProfilePage","mainEntity":{"@type":"Person","name":"Some One",
 "jobTitle":"Engineer","sameAs":["https://github.com/someone"],
 "knowsAbout":[{"@type":"Thing","name":"Search","sameAs":["https://www.wikidata.org/entity/Q816826"]}]}}
</script></head><body><div class="h-card"><a class="p-name u-url" href="/">Some One</a> <p>Engineer</p></div></body></html>"""
RESUME_JSON = json.dumps({"basics": {"name": "Some One"}, "work": [{"name": "Acme", "position": "Engineer"}]})


class CheckTest(unittest.TestCase):
    def site(self, pages):
        self.fetched = []

        def fake(url):
            self.fetched.append(url)
            return url, pages.get(url.split("someone.example", 1)[-1])
        check.fetch = fake

    def by_key(self, result):
        return {c["key"]: c for c in result["checks"]}

    def test_full_site_scores_five(self):
        self.site({"/": HOME, "/resume": RESUME, "/resume.json": RESUME_JSON})
        result = check.check("someone.example/")
        self.assertEqual(5, result["score"])
        self.assertEqual(["https://someone.example/", "https://someone.example/resume",
                          "https://someone.example/resume.json"], self.fetched)
        self.assertEqual("Some One", self.by_key(result)["h_card"]["found"])
        self.assertEqual(["https://someone.example/feed.xml"], result["feeds"])

    def test_bare_site_scores_zero(self):
        self.site({"/": "<html><body><p>Hello</p></body></html>"})
        result = check.check("https://someone.example/")
        self.assertEqual(0, result["score"])
        self.assertTrue(all(not c["pass"] for c in result["checks"]))

    def test_unreachable_site_is_an_error_not_a_crash(self):
        self.site({})
        self.assertIn("error", check.check("someone.example/"))

    def test_taxonomy_ids_in_resume_json_count(self):
        skills = {"basics": {"name": "S"}, "skills": [{"name": "AI", "sameAs": ["https://www.wikidata.org/entity/Q11660"]}]}
        self.site({"/": HOME, "/resume.json": json.dumps(skills)})
        checks = self.by_key(check.check("someone.example/"))
        self.assertTrue(checks["taxonomy"]["pass"])
        self.assertFalse(checks["person"]["pass"])

    def test_broken_json_ld_and_resume_are_ignored(self):
        bad = '<html><head><script type="application/ld+json">{not json</script></head><body></body></html>'
        self.site({"/": bad, "/resume.json": "<html>not json</html>"})
        self.assertEqual(0, check.check("someone.example/")["score"])


if __name__ == "__main__":
    unittest.main()
