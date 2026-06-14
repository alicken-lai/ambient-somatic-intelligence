# DMN Sync Manifest Dry Run

Phase: 1G.6 DMN Governance Example Wrappers and Sync Manifest Dry Run  
Date: 2026-06-10  
Status: Dry run only. No synchronization is authorized.

## Purpose

This document explains the synthetic dry-run sync manifest:

`examples/dmn_governance/sync_manifest_home_to_office.example.json`

The manifest demonstrates how Home Hermes could evaluate records before sending summaries to Office Hermes without mutating either node.

## Dry-Run Controls

The manifest includes:

- `sync_mode = dry_run`
- `no_mutation = true`
- source node and target node
- allowed records
- excluded records
- exclusion reasons
- privacy filters
- governance filters
- conflict candidates
- replay references

## Allowed Records

Two synthetic records would be eligible in summary form:

1. Guardian-reviewed WiFi CSI promotion example.
2. Consolidated temperature and humidity trend example.

Both are internal, synthetic, replay-referenced, and not raw streams.

## Excluded Records

The dry run excludes:

- the unresolved Home Hermes power conflict record;
- a synthetic raw WiFi CSI window standing in for restricted raw stream data.

Reasons include unresolved conflict, raw or restricted payload, and missing human review for sync.

## Filters Applied

Privacy filters:

- exclude restricted records;
- exclude raw streams;
- use summary-only form for internal records.

Governance filters:

- require source node;
- require replay pointer;
- require governance state not raw;
- block unresolved conflicts.

## Replay Preservation

Allowed records include replay IDs and checksums. This lets a receiving node inspect provenance before trusting or promoting the memory.

## No Production Behavior

This manifest does not:

- read real DMN memory;
- write real DMN memory;
- start synchronization;
- create sync adapters;
- authorize cross-node transfer;
- alter Guardian, runtime, replay, governance code, or schemas.

## Next Schema Need

A future sync manifest schema should validate:

- node identity;
- allowed and excluded record lists;
- filter names;
- conflict candidates;
- replay references;
- mutation count equals zero for dry-run manifests.
