# Field guide

The field map and research loop are original editorial syntheses of LLM-based social simulation, informed by the sources below. They connect individuals and cognition, interactions and experiments, and collective dynamics; collective context also shapes individual behavior. Control, calibration, and evaluation apply across these scales. The map provides an orientation to the field, while this repository covers selected research rather than an exhaustive taxonomy.

The research loop connects human evidence, agent and environment design, simulated behavior, and evaluation, with feedback into model revision. Plausible output alone does not establish fidelity: evidence must support the particular population, setting, and behavior being modeled. The background readings below support this orientation and remain separate from the curated research entries and their paper counts.

## Background reading

- Xinyi Mou et al. (2024). [From Individual to Society: A Survey on Social Simulation Driven by Large Language Model-based Agents](https://arxiv.org/abs/2412.03563). Organizes the literature into individual, scenario, and society simulation.
- Chen Gao et al. (2024). [Large language models empowered agent-based modeling and simulation: a survey and perspectives](https://www.nature.com/articles/s41599-024-03611-3). *Humanities and Social Sciences Communications*, 11, 1259. Explains agents, environments, interactions, and challenges in building and evaluating simulations.
- Maik Larooij and Petter Törnberg (2026; published online 2025). [Validation is the central challenge for generative social simulation: a critical review of LLMs in agent-based modeling](https://link.springer.com/article/10.1007/s10462-025-11412-6). *Artificial Intelligence Review*, 59, 15. Examines whether validation supports a simulation's intended purpose and target system.

## Maintenance

Edit the source assets in [`site/static/assets/field-map.svg`](../site/static/assets/field-map.svg) and [`site/static/assets/research-loop.svg`](../site/static/assets/research-loop.svg); [`scripts/build.py`](../scripts/build.py) embeds them in the website. Keep the SVG titles, descriptions, labels, and the accompanying text captions consistent.

Green links in the field map open existing catalogue topics: `silicon-participants`, `social-experiments`, `multi-agent`, `control-calibration`, and `evaluation`. Keep their `data-topic` values and URL parameters aligned with [`data/topics.json`](../data/topics.json). The links are reading entry points, not an assertion that each topic belongs to only one scale.
