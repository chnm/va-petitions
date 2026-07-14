# Records of Revolution: Project Roadmap

Last updated: July 14, 2026

This document preserves the current design, data, and implementation context for
future work sessions. Read it alongside the open GitHub issues before changing
the geography model or preparing the current redesign for review.

## Current Branch

- Branch: `codex/blue-hero-refresh`
- Base: `main`
- Purpose: site-wide visual refresh, new project identity, catalog-link safety,
  and improvements to the Catalogue, Map, Search, and footer.

## Current Product Direction

### Identity and visual system

- Project title: **Records of Revolution**
- Homepage subtitle: **War, Rights, Family, and Freedom in Virginia's Legal
  Records.**
- Interior pages use full-width iron-gall blue heroes with left-aligned content.
- The homepage uses a split hero with a real 1776 petition scan. The image links
  to its Library of Virginia catalog record. Keep this version while awaiting PI
  feedback.
- Blue is the structural/state color, rust is reserved for voice and emphasis,
  and ochre is used on blue fields.
- The homepage statistics remain in their own paper-colored band rather than
  inside the hero.

### Terminology

- **The Catalogue** means this site's browse interface.
- **Online catalog** means the Library of Virginia's external catalog.
- The navigation item **About** links to the `#about` section on the homepage.
- Avoid references to Virginia Memory in public copy. Legacy essay links are
  resolved through imported Library catalog permalinks when possible.

### Collection access

- Catalogue and Search rows are fully clickable when a Library permalink is
  available.
- Unavailable records remain non-interactive and display **Coming Soon**.
- Catalogue filtering, sorting, and pagination return users to the results
  section rather than the top of the page.
- Search supports word-order-independent terms, common connective words, years,
  subject filters, and exact source-locality filters.

### Accessibility baseline

- Body and interface typography has been enlarged for older users and
  genealogists.
- Native select menus use a cross-browser closed-control treatment with 16px
  text, a 44px minimum target, visible focus, and forced-colors fallback.
- The full accessibility audit is deliberately deferred to a separate branch.

## Geography and Locality: Important Distinctions

The current Map and homepage count different geographic concepts:

- Homepage: **113 Named Localities**, calculated from `Petition.locality_raw`,
  splitting compound semicolon values and excluding `Unknown`.
- Map: up to **314 modern locality assignments**, derived from the expanded
  `County` relationships and modern centroids.
- Historical boundaries: fetched year-by-year from the Atlas of Historical
  County Boundaries API, but currently rendered only as a visual overlay.

Do not change the Map count to 114 as a cosmetic fix. The underlying locality
model must be decided and explained first.

### Historical data already present in the source CSV

The source file `LVAdocuments_GMU.xlsx - AllRecords.csv` contains:

- `LOCALITY_NUMBER` for 3,765 records, with 196 distinct values. These appear to
  be time-specific historical-boundary assignments created by Eric Roeberg.
- `VA_Historical_Counties_GDB_Name`, but its exported populated values are
  `#ERROR!` and cannot currently be used.
- 3,708 complete dates, 17 year-only dates, 33 approximate or partial dates,
  and 9 blank dates.

Eric is expected to provide a crosswalk connecting `LOCALITY_NUMBER` to
historical names, effective date spans, geometries or stable geometry IDs,
centroids, and jurisdictions. Do not infer this mapping without that crosswalk.

### Proposed future Geography modes

The agreed direction is one coordinated Geography interface with three modes:

1. **Modern localities** - default mode using the existing modern assignments.
2. **Historical counties** - year-specific boundaries and historical centroids.
3. **Locality list** - exact source labels, indexing compound records under each
   constituent locality while preserving the original displayed label.

The geographic scope should continue to include Virginia and the territories
represented by the current project: Virginia, West Virginia, Kentucky, and
Pennsylvania where relevant.

An exploratory interaction in issue #7 proposes a **Plot records by** control:

- Historical county at record date
- Modern county assignments

Possible transitions include moving historical centroid points to modern
assignments and briefly drawing connector lines. This remains a prototype idea,
not an implementation requirement.

The major unresolved design question is whether Historical mode should:

- show one boundary year and only records from that year; or
- show a selected boundary year with a separate record-date range.

## Open GitHub Issues

- [#7 - Design modern, historical, and source-locality geography modes](https://github.com/chnm/va-petitions/issues/7)
- [#9 - Use light four-color fills for historical county boundaries](https://github.com/chnm/va-petitions/issues/9)
- [#10 - Add zoom-aware labels to historical county boundaries](https://github.com/chnm/va-petitions/issues/10)
- [#6 - Run responsive visual regression across primary pages](https://github.com/chnm/va-petitions/issues/6)
- [#8 - Review and clean up blue hero refresh branch before PR](https://github.com/chnm/va-petitions/issues/8)

Issue #7 is the umbrella geography issue. Expand it or create implementation
sub-issues after the crosswalk arrives and the boundary-year interaction is
decided.

## Current Map Behavior

- Leaflet with CARTO basemap tiles.
- Modern county circle markers and ranked locality panel.
- Subject and two-ended record-year filters.
- Historical boundary overlay uses the upper end of the selected year range.
- Locality list sorts by record count or alphabetically without changing bar
  scale.
- A modal explains current Map behavior and interpretive limits.

## Before Opening a Pull Request

Follow issues #6 and #8:

1. Review desktop, laptop, tablet, and mobile layouts for every primary page.
2. Check Safari and Chrome dropdowns, focus states, and navigation wrapping.
3. Verify Map sorting, filters, dialog, boundary loading, and responsive panels.
4. Verify Catalogue and Search linked/unavailable row states.
5. Confirm footer logo balance and homepage hero image behavior.
6. Review the complete branch diff for obsolete markup, styles, and unused
   assets.
7. Rebuild Tailwind and run all checks.

## Verification Commands

```bash
.venv/bin/python manage.py tailwind build
.venv/bin/python manage.py check
.venv/bin/python manage.py test
git diff --check
```

At the time of this handoff, the suite contains 17 passing tests.

## Suggested Next Session

1. Read this roadmap and issues #6, #7, and #8.
2. Run `git status -sb` and the verification commands.
3. Complete the responsive visual-regression issue.
4. Clean the branch and prepare a pull request.
5. Treat PI feedback on the homepage hero as a targeted follow-up.
6. Defer the larger historical-geography implementation until the Eric
   crosswalk is available.
