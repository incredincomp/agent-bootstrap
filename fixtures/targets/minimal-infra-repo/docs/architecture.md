# Architecture Overview

This document describes the high-level architecture of the minimal-infra-repo fixture.

This is a **fixture file** — minimal and intentional. Not real infrastructure documentation.

---

## System overview

A single-environment (dev) infrastructure setup using Terraform.

```
environments/
  dev/   — development environment resources
```

## Cloud provider

None (fixture placeholder). A real repo would specify AWS, GCP, Azure, or similar.

## Components

| Component | Purpose |
|-----------|---------|
| (none declared) | Fixture only — extend with real resources |

## Deployment model

Manual Terraform apply from the `environments/dev/` directory.

## Key decisions

- Use environment-specific `.tfvars` files to separate config from code.
- Keep each environment in its own subdirectory for isolation.
