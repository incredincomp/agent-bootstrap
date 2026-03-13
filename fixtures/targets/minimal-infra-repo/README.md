# minimal-infra-repo

A minimal infrastructure repository. Used as a fixture target for bootstrap self-tests.

This is a **fixture repository** — intentionally minimal and not production infrastructure.

## Purpose

Demonstrates a documentation/infrastructure-oriented target repository shape for the
agent-bootstrap self-test harness.

## Stack

- Terraform (infrastructure-as-code)
- No application runtime
- Markdown documentation

## Structure

```
docs/
  architecture.md            — System architecture overview
environments/
  dev/
    placeholder.tfvars.example — Example Terraform variable definitions
```

## Usage

```bash
# Initialize Terraform (dev environment)
cd environments/dev
terraform init
terraform validate

# Review planned changes
terraform plan -var-file=placeholder.tfvars.example
```
