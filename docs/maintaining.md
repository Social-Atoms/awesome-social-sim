# Maintenance and deployment

The repository is the source for both the GitHub reading list and the website at **https://social-atoms.github.io/awesome-social-sim/**. GitHub Pages serves the generated static files; no application server, database, or package installation is needed.

## How a change reaches readers

1. A contributor submits an issue or pull request.
2. A maintainer reviews inclusion, sources, and the generated Markdown diff. Automated validation checks the data and build behavior.
3. Merging into `main` triggers the Pages workflow. It rebuilds `dist/`, uploads the site artifact, and deploys to the `github-pages` environment.
4. The successful deployment in the repository's **Actions** tab records the published URL and commit.

Pull requests validate changes without publishing them. For a deployment failure, inspect the workflow's failing step and rerun the job after fixing its cause; a local build alone does not mean the public website has updated.

## Set up GitHub Pages

Repository administrators only need to configure this once:

1. Open **Settings → Pages** in this repository.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Ensure GitHub Actions is enabled for the repository and the Pages workflow is allowed by the organization's Actions policy.
4. Push or merge a change to `main`, or run the Pages workflow manually from **Actions**.
5. Confirm that deployment succeeds and the repository's Pages settings show the site URL.

The deployment workflow uses GitHub's Pages artifact and deployment actions with the required Pages and OIDC permissions. It does not need a personal access token, a `gh-pages` branch, or a checked-in `dist/` directory. Preserve the workflow's separation between validation and deployment permissions.

For a fork, enable Pages in the fork's settings and update the repository and website links before publishing it. The default project-site URL contains the repository name as a path segment.

## Review a catalogue contribution

- Confirm it fits the scope in [CONTRIBUTING.md](../CONTRIBUTING.md), and check that another version is not already listed.
- Open the paper and publication or acceptance evidence. Match the title, venue, year, and track; distinguish a standalone preprint from an accepted paper.
- Check each chosen topic and inclusion note. Summaries should accurately describe a demonstrated result or clearly identify a proposal.
- Keep awards and workshop history separate from the basis for inclusion, with supporting sources.
- Review the generated changes. Topic counts and total counts should come from the data, and the paper should appear once in each selected topic.

The build validates structure and consistency. It does not establish scientific validity, verify a venue's decision, or guarantee that external links remain available. Those checks require source review.

## Local checks and preview

Use Python 3.11 or newer:

```sh
python3 scripts/build.py
python3 scripts/build.py --check
python3 -m unittest discover -s tests
python3 -m http.server 4173 --directory dist
```

Open [localhost:4173](http://localhost:4173/). For website edits, also check search, combined filters, a shared filter URL, mobile layout, and keyboard navigation. The full catalogue should remain readable with JavaScript disabled.

The build copies `site/static/` into `dist/` and renders `site/index.template.html` as `dist/index.html`. It also updates `tags/*.md` and the block between `<!-- catalogue:start -->` and `<!-- catalogue:end -->` in `README.md`. Only edit the source files; commit generated Markdown alongside a data change and leave `dist/` untracked.

Keep asset references relative, such as `assets/social-atoms.svg`, so the website works under `/awesome-social-sim/` as well as at a local preview's root. Avoid hard-coded local hosts, filesystem paths, and root-relative asset URLs. The hosting output includes `.nojekyll` for static delivery.

## Publication and topic updates

When an accepted paper gains a proceedings page, update its existing JSON record, provenance, year, and venue label. Preserve its ID and useful secondary links. Update the catalogue date, then regenerate the Markdown and website.

Discuss new topics before adding them. A useful topic should have a clear boundary and help readers find related work; avoid creating a topic for a single incidental keyword. If a topic ID changes, update every membership and inclusion-note key together.

The bundled font's license and the origin of the brand assets are recorded in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). Keep notices with their assets when modifying the build or distribution.
