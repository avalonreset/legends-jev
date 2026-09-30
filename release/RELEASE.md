# Release candidate: `legends-jev v0.1.0`

Publication is not performed by this candidate. Local installation and local
guide discovery are supported before public release. The public manager catalog
requires a real public release, full commit and exact downloaded archive hash.
`catalog-entry.candidate.json` deliberately has null pins and is NOT an active
catalog. Do not insert placeholders in the live catalog.

## Final publication sequence

1. Review source, tests, benchmark report and artifact contents. Review MIT
   licensing and the independent TypeSafe service boundary. Confirm public
   repository owner `avalonreset/legends-jev` before creating it.
2. Publish the reviewed repository, tag `v0.1.0`, and create the GitHub release
   using `release/NOTES.md`. Attach wheel, sdist and their SHA256 sums.
3. Resolve the tag to its full commit; download the public codeload ZIP at that
   commit and hash its actual bytes. Populate candidate pins from those facts.
4. Add the entry to `cto-legends/cto_legends/catalog.json`, choose the next live
   catalog version at publication time, and add its changelog. Run router tests.
5. From a fresh manager home, preview/sync/apply, install this module, run doctor,
   check handoff files and ordinary outcome routing, and confirm check-updates.
6. Push the reviewed catalog change. Refresh existing startup indexes through
   manager sync. Verify fresh-session discovery separately from index presence.

No manager code change or new skill registration is needed. The current
supported local-guide route cannot lexically match ordinary outcome phrases;
the local startup instruction supplies that consideration until public catalog
admission. A fresh public-download install and remote CI remain publication-time
checks. Do not call them passed based on local fixtures.
