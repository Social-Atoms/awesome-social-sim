# Catalogue data format

Each paper has one UTF-8 JSON file at `data/papers/<id>.json`. The filename must match the record's `id`. The build validates these records and generates the website, topic pages, and README catalogue block from the same data.

## Required fields

| Field | Meaning |
| --- | --- |
| `id` | Stable lowercase, hyphen-separated identifier. Keep it when metadata or the title changes. |
| `title` | The paper's full title, using its publication's capitalization. |
| `url` | Canonical HTTPS paper link. Prefer proceedings or a publisher page; use a preprint only for accepted work awaiting proceedings. |
| `venue` | Human-readable venue and year. Include `Accepted` if proceedings are not yet available, identify a position track when applicable, and distinguish ACL-family Main from Findings. |
| `year` | Integer publication year or accepted venue's year. |
| `tags` | Nonempty list of distinct topic IDs from [`topics.json`](../data/topics.json). |
| `primaryTopic` | One of the record's tags; determines the default description shown on the website. |
| `notes` | Object with exactly one short inclusion note for each tag, keyed by that tag's ID. |

This existing Character-LLM record demonstrates the minimum shape:

```json
{
  "id": "character-llm-a-trainable-agent-for-role-playing",
  "title": "Character-LLM: A Trainable Agent for Role-Playing",
  "url": "https://aclanthology.org/2023.emnlp-main.814/",
  "venue": "EMNLP 2023 Main",
  "year": 2023,
  "tags": ["control-calibration", "silicon-participants"],
  "primaryTopic": "control-calibration",
  "notes": {
    "control-calibration": "Controls a simulated character through experience reconstruction and character-specific fine-tuning.",
    "silicon-participants": "Trains personal simulacra from character profiles, experiences, and emotional states."
  }
}
```

The record already exists; edit it in place rather than adding a duplicate. For a new entry, also supply the source evidence described below.

## Optional fields

| Field | Meaning |
| --- | --- |
| `kind` | Short type label, such as `Benchmark` or `Position paper`. |
| `authors` | Nonempty list of author names in publication order. Supply the complete list when adding it. |
| `equalContributors` | Number of leading authors with equal contribution; integer from 2 through the length of `authors`. Omit if this representation does not fit the paper. |
| `resources` | Nonempty list of objects with distinct `label` and HTTPS `url` values, for example `arXiv`, `Project`, `Code`, or `Benchmark`. |
| `publicationHistory` | Concise publication history, such as earlier workshop appearances. |
| `historySource` | HTTPS source supporting `publicationHistory`; include the history text as well. |
| `provenance` | Source and verification details, described below. |

Do not invent missing author information, links, distinctions, or publication history. Omit unknown optional fields rather than setting them to `null`. JSON does not support comments. Unknown fields are rejected to catch spelling mistakes.

Resource links appear under the paper title on both the website and GitHub topic pages. Include the paper's arXiv record, official code, project page, or replication data when available. Verify the connection using the paper, an author-maintained project page, or the repository's citation; do not add unofficial forks or guessed URLs. Use concise labels such as `arXiv`, `Code`, `Project`, and `Data`, and omit links that duplicate the main publication URL.

## Source and verification details

`provenance` supports these fields:

| Field | Meaning |
| --- | --- |
| `addedAt` | Date first added, in `YYYY-MM-DD` format. |
| `checkedAt` | Date the supporting metadata was last checked, in the same format. |
| `source` | Brief editorial context about the source or verification. |
| `publicationSource` | HTTPS URL supporting publication or acceptance at the stated venue. |
| `descriptionSource` | HTTPS URL for the paper or official abstract supporting the inclusion notes. |
| `authorSource` | HTTPS URL supporting names, order, and any equal-contribution information. |
| `workshopSources` | List of HTTPS URLs supporting earlier workshop appearances. |

For example, the official publication page for Character-LLM can support both its venue and its description. Add the following `provenance` object to the record:

```json
{
  "provenance": {
    "checkedAt": "2026-09-21",
    "publicationSource": "https://aclanthology.org/2023.emnlp-main.814/",
    "descriptionSource": "https://aclanthology.org/2023.emnlp-main.814/"
  }
}
```

Use the actual date you checked the sources. For an accepted paper, the evidence must explicitly establish acceptance; an arXiv submission alone does not. When proceedings appear, replace the main `url`, update the `venue`, `year`, and provenance, and preserve the same paper ID and useful secondary links under `resources`.

## Topics and collection metadata

[`data/topics.json`](../data/topics.json) is an ordered list of objects containing `id`, `label`, and `description`. Its order determines navigation and topic presentation. Stable IDs also support shared filter URLs, so renaming one requires updating every affected record and reviewing those links.

[`data/collection.json`](../data/collection.json) contains `updatedAt`, the date of the last catalogue update. Counts are derived from the records, not entered manually. A paper in two topics counts once toward the collection total and once in each topic.

Run `python3 scripts/build.py` after editing data. Run `python3 scripts/build.py --check` to verify that the checked-in Markdown matches the source records.
