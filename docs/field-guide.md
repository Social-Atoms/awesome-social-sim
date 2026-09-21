# Field guide

One map connects what social simulation studies with how its claims are tested. Individuals, interactions, and societies are related scales, not numbered stages: people shape collective patterns, and social context shapes individual behavior.

Human evidence, calibration, and evaluation form a shared foundation across all three scales. The map is an editorial orientation to LLM-based social simulation, not an exhaustive taxonomy. Plausible behavior alone does not establish fidelity to a population or setting.

## Background reading

- Xinyi Mou et al. (2024). [From Individual to Society: A Survey on Social Simulation Driven by Large Language Model-based Agents](https://arxiv.org/abs/2412.03563). Organizes the literature into individual, scenario, and society simulation.
- Chen Gao et al. (2024). [Large language models empowered agent-based modeling and simulation: a survey and perspectives](https://www.nature.com/articles/s41599-024-03611-3). *Humanities and Social Sciences Communications*, 11, 1259. Explains agents, environments, interactions, and challenges in building and evaluating simulations.
- Maik Larooij and Petter Törnberg (2026; published online 2025). [Validation is the central challenge for generative social simulation: a critical review of LLMs in agent-based modeling](https://link.springer.com/article/10.1007/s10462-025-11412-6). *Artificial Intelligence Review*, 59, 15. Examines whether validation supports a simulation's intended purpose and target system.

## Maintenance

Edit [`site/static/assets/field-map.svg`](../site/static/assets/field-map.svg); [`scripts/build.py`](../scripts/build.py) embeds the map in the website. Its [mobile layout](../site/static/assets/field-map-mobile.svg) presents the same concepts vertically. Keep its title, description, labels, and accompanying caption consistent. The README uses a compact companion illustration in light and dark variants in [`docs/assets/`](assets/).

The map and topic navigation share the same five filters. Each SVG link's `data-topic` and URL query must match an ID in `data/topics.json`. Clicking a map tag clears search and year restrictions, updates the URL and selection, and moves focus to the paper list; All papers clears the topic too. Both SVG layouts expose the same links, including when opened as standalone files.

Topics are reading entry points that can span several scales, not exclusive categories within the map. The three scale links lead to Silicon participants, Social science experiments, and Multi-agent interaction; The shared Human evidence → Model → Simulate → Evaluate cycle applies across scales, with Calibrate feeding back into Model. Evaluate opens Evaluation; Calibrate opens Control and calibration. Background readings are separate from the curated entries and their paper counts.
