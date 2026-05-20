# Civilization Agency Risk Map — v0.7.7

| Runtime | Role | Agency risk | Guardian |
|---------|------|-------------|----------|
| ambient | local_agency_boundary | low (bounded) | required |
| hermes | orchestration_client | medium (routing) | required |
| foreign | advisory_peer_agency | high (untrusted) | observational only |

## Containment zones

1. **Constitutional** — `constitutional_agency_boundary.py`
2. **Cognition** — `cognition_containment.py`
3. **Provenance** — `agency_provenance.py` + `agency_lineage.py`
4. **Retention** — `cognition_retention_boundary.py`
