# How to add each piece

Replace every value with the person's own. Do them in this order; each one stands alone.

## 1. rel="me" links

In the `<head>` of every page, one line per profile:

```html
<link rel="me" href="https://www.linkedin.com/in/you">
<link rel="me" href="https://github.com/you">
```

Then the person puts their site's address in each of those profiles (the website field).
The link going both ways is the proof; only they can do the second half. Check whether a
profile already links back before asking (GitHub's public API shows the `blog` field).

## 2. schema.org Person

On the home page or the resume page:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ProfilePage",
  "mainEntity": {
    "@type": "Person",
    "@id": "https://example.com/#me",
    "name": "Your Name",
    "jobTitle": "Your Title",
    "url": "https://example.com",
    "sameAs": ["https://www.linkedin.com/in/you", "https://github.com/you"]
  }
}
</script>
```

Keep one `@id` for the person and reuse it on every page. Current jobs go in `worksFor` as
`EmployeeRole` (with `roleName`, `startDate`); past jobs in `alumniOf` as `OrganizationRole`
(with `startDate`, `endDate`). Dates are `YYYY-MM`. Validate at validator.schema.org.

## 3. JSON Resume at /resume.json

Format: https://jsonresume.org/schema (v1.0.0). Minimum useful file:

```json
{
  "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json",
  "basics": { "name": "Your Name", "label": "Your Title", "url": "https://example.com",
              "profiles": [{ "network": "GitHub", "username": "you", "url": "https://github.com/you" }] },
  "work": [{ "name": "Company", "position": "Title", "startDate": "2019-12", "endDate": "2022-03" }],
  "education": [{ "institution": "School", "area": "Subject" }],
  "skills": [{ "name": "Search" }]
}
```

Serve it as `application/json`, generate it from the same data as the resume page, and link
it from that page: `<link rel="alternate" type="application/json" href="/resume.json">`.
Validate it against the schema file above.

## 4. Skills with taxonomy ids

Keep the person's own words as `name`; add the shared definition as `sameAs`:

```json
"knowsAbout": [
  { "@type": "Thing", "name": "Search", "sameAs": ["https://www.wikidata.org/entity/Q816826"] }
],
"hasOccupation": {
  "@type": "Occupation", "name": "Product manager",
  "sameAs": "http://data.europa.eu/esco/occupation/9f508305-80ce-4111-8722-f2c9b4a44890"
}
```

Where to look ids up (always look up, never recall):

- **Wikidata**, for topics: `https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&search=<term>`.
  Read the description; many terms have several entries.
- **ESCO**, for occupations and skills: `https://ec.europa.eu/esco/api/search?text=<term>&type=occupation&language=en`
  (or `type=skill`). Coverage of skills is uneven; skip a skill with no close match.
- **O\*NET** (US) covers occupations but has gaps: it has no product manager, for example.

The same `sameAs` list can go on each entry in `resume.json` `skills`.

## 5. h-card

Class names on the HTML that is already there:

```html
<header class="h-card">
  <a class="p-name u-url" href="https://example.com/">Your Name</a>
  <p class="p-job-title">Your Title</p>
  <span class="p-locality">City</span>, <span class="p-region">ST</span>
  <a class="u-url" rel="me" href="https://github.com/you">GitHub</a>
</header>
```

If the name becomes a link, keep its look with `color: inherit; text-decoration: none`.

## Not scored, worth doing

Advertise a feed so people can follow new posts:
`<link rel="alternate" type="application/rss+xml" title="Blog" href="/feed.xml">`.
