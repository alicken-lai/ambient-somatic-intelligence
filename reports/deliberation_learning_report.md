# Deliberation Learning Report

## Most Effective Modes

| Task Class | Samples | Best Mode | Single | Light | Full | Avg ROI |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| memory_mutation | 3 | single | 71.35 | 71.35 | 71.35 | 0.00 |
| state_changing | 3 | single | 71.35 | 71.35 | 71.35 | 0.00 |
| implementation_review | 4 | full | 66.40 | 70.20 | 70.72 | 4.06 |
| credential_sensitive | 3 | full | 64.75 | 69.82 | 70.52 | 5.42 |
| architecture | 3 | light | 51.55 | 68.85 | 68.85 | 17.30 |
| debugging | 3 | full | 51.55 | 67.45 | 68.85 | 16.60 |
| provider_policy | 3 | light | 51.55 | 68.85 | 68.85 | 17.30 |
| research_analysis | 3 | full | 51.55 | 66.75 | 68.85 | 16.25 |

## Highest ROI Task Classes

- architecture: avg ROI 17.30, best mode light
- provider_policy: avg ROI 17.30, best mode light
- debugging: avg ROI 16.60, best mode full
- research_analysis: avg ROI 16.25, best mode full
- credential_sensitive: avg ROI 5.42, best mode full

## Recommended Routing Changes

- architecture: default `light` (confidence 0.95) - light beats single by 17.30 points across 3 samples.
- debugging: default `full` (confidence 0.95) - full beats single by 17.30 points across 3 samples.
- provider_policy: default `light` (confidence 0.95) - light beats single by 17.30 points across 3 samples.
- credential_sensitive: default `full` (confidence 0.724) - full beats single by 5.77 points across 3 samples.
- research_analysis: default `full` (confidence 0.95) - full beats single by 17.30 points across 3 samples.
- implementation_review: default `full` (confidence 0.698) - full beats single by 4.32 points across 4 samples.

## Safety Boundary

Adaptive routing may change mode selection, child selection, and verification depth. It may not change Guardian rules, provider permissions, credential access policies, memory write policies, or human approval requirements.
