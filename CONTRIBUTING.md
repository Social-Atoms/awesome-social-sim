# Contributing

Help readers find research that makes a clear, evidence-backed contribution to social simulation. Suggestions, factual corrections, clearer inclusion notes, and accessibility improvements are welcome.

## Suggest a paper without code

1. Check the [website](https://social-atoms.github.io/awesome-social-sim/) or search [`data/papers/`](data/papers/) to avoid a duplicate. Different versions of the same paper belong in one record.
2. Open a [paper suggestion](https://github.com/Social-Atoms/awesome-social-sim/issues/new?template=paper-suggestion.yml). Include the title, publication or acceptance source, relevant topics, and a short explanation of its contribution.
3. A maintainer checks scope and sources before adding it. Suggestions are reviewed on their merits; inclusion is not automatic.

For an existing entry, use the [correction form](https://github.com/Social-Atoms/awesome-social-sim/issues/new?template=correction.yml) and link to evidence for the replacement.

## What we include

- Published or accepted original research and benchmarks in a main conference track or established journal.
- Selected position papers that directly address how to build, understand, or evaluate social simulations. Label their proposals as proposals.
- Work about simulated human behavior, social interaction, or collective dynamics, including methods that test fidelity to human evidence.

We currently exclude standalone preprints, workshop-only papers, surveys, and general-purpose multi-agent task solving. A preprint URL is acceptable for an accepted paper before proceedings exist, provided acceptance is verifiable and the entry explicitly says **Accepted**. Prior workshop appearances can be recorded as history; they do not by themselves qualify a paper for inclusion.

Use the formal publication year, or the accepted venue's year, rather than the year of the first preprint. Prefer proceedings, publisher pages, official venue decisions, and authoritative project or institutional records. Do not infer acceptance from a submission or an event logo. Award claims need their own supporting source.

## Add or correct a paper with a pull request

Requires Python 3.11 or newer; no dependency installation is needed.

1. Fork the repository and create a branch for your change.
2. Add or edit **one JSON file per paper** under `data/papers/`. Use an existing record as a starting point and follow the [data format](docs/data-format.md). Set all relevant `tags`, select one `primaryTopic`, and give each tag a concise inclusion note.
3. For a new paper or a publication-status change, record a `provenance.publicationSource` and `provenance.checkedAt` date. Use `descriptionSource` for the paper underlying your summary. Existing records may be less complete; incremental improvements are welcome.
4. Update `updatedAt` in `data/collection.json` to the date of the catalogue change (`YYYY-MM-DD`). Do not change it for a styles-only edit.
5. Generate the website and Markdown pages, then run the checks:

   ```sh
   python3 scripts/build.py
   python3 scripts/build.py --check
   python3 -m unittest discover -s tests
   ```

6. Review your diff. Commit the JSON changes and the generated changes to `tags/*.md` and the catalogue block in `README.md`. **Do not commit `dist/`.** Avoid editing the generated Markdown by hand; the next build will overwrite it.
7. Open a pull request with the publication evidence and a short explanation of the change. Keep unrelated papers or layout changes in separate pull requests when practical.

One record feeds all topic pages and the website. You do not need to copy the paper into several Markdown files.

## Write useful inclusion notes

Explain what the paper contributes to the selected topic in one or two specific sentences. Name the behavior, method, or evaluation when possible. Use neutral language and preserve the paper's limits; a benchmark score or plausible output does not establish fidelity to real human behavior.

For example, Character-LLM's control note is:

> Controls a simulated character through experience reconstruction and character-specific fine-tuning.

Notes may differ across topics. Avoid promotional claims, copied abstracts, acceptance-rate rankings, and vague descriptions such as “an important multi-agent paper.” Choose topics based on the main contribution rather than incidental keywords. Propose a new topic in an issue before reorganizing existing entries.

## Website and tooling changes

Edit `site/index.template.html` or files under `site/static/`, then run the same build and checks above. Preview with:

```sh
python3 -m http.server 4173 --directory dist
```

For interface changes, check a narrow mobile viewport, keyboard focus and filter navigation, and that the full catalogue remains readable without JavaScript. Include a screenshot when it makes the change easier to review. Keep asset URLs relative so the site works under GitHub Pages' `/awesome-social-sim/` path.

Pull requests run validation only. Publication happens after changes land on `main`. Maintainers can follow [maintenance and deployment](docs/maintaining.md) for review and release details.
