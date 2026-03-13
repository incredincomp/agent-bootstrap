# Example Notes: Infrastructure Repository

This document guides an agent performing discovery or bootstrap on an infrastructure-as-code (IaC) repository.

---

## Likely repository characteristics

- Primary language: HCL (Terraform), YAML (CloudFormation, Ansible), or a mix
- Common tools: Terraform, Pulumi, AWS CDK, Ansible, Helm, Kustomize
- Package/module management: Terraform modules (local or registry), Helm chart dependencies (`Chart.yaml`)
- State management: Remote state (S3 + DynamoDB, GCS, Terraform Cloud) or local (development only)
- CI/CD: GitHub Actions or Jenkins running `terraform plan` on PR, `terraform apply` on merge
- Test tools: `terratest` (Go), `checkov`, `tflint`, `conftest` (OPA), `kitchen-terraform`
- Common structure:
  - `modules/` — reusable Terraform/Pulumi modules
  - `environments/` or `stacks/` — per-environment configs
  - `scripts/` — helper scripts (bootstrap, teardown, secret rotation)
  - `docs/` — architecture diagrams, runbooks

---

## What an agent should prioritize in discovery

1. **State backend:** Find `backend.tf` or equivalent — this is critical. Remote state location determines blast radius of any change.
2. **Environment separation:** Is there a `dev/`, `staging/`, `prod/` structure? Are environments separated by directory, workspace, or variable file?
3. **Module dependencies:** Identify which modules are local vs. registry-sourced. Local modules are in-scope; registry modules are not.
4. **CI pipeline:** The CI config reveals what commands run automatically — `plan` vs. `apply` triggers are especially important.
5. **Secrets management:** Look for references to AWS Secrets Manager, HashiCorp Vault, SOPS, or `terraform.tfvars` (check for `.gitignore` exclusion).
6. **Provider versions:** Check `versions.tf` or `required_providers` — version constraints matter for compatibility.
7. **Existing runbooks:** Check `docs/` for teardown, DR, or rotation procedures that constrain what can be safely changed.

---

## Typical authoritative files

| File | Why authoritative |
|------|------------------|
| `backend.tf` / `backend.hcl` | Remote state configuration — do not change without team coordination |
| `versions.tf` | Provider and Terraform version constraints |
| `variables.tf` | Public interface of a module — defines inputs |
| `outputs.tf` | Public interface of a module — defines outputs |
| `terraform.tfvars` or `*.auto.tfvars` | Environment-specific variable values (check if gitignored) |
| `.tflint.hcl` | Linting rules |
| `Chart.yaml` (Helm) | Chart metadata and dependency declarations |

---

## Common traps

- **Applying vs. planning:** Never run `terraform apply` (or equivalent) without explicit authorization. Discovery is read-only.
- **Shared state:** Multiple environments may share a state file — changes to one module can affect others unexpectedly.
- **tfvars not in repo:** Secret-containing `.tfvars` files are often gitignored. The agent will not see them — note this as a gap.
- **Workspace confusion:** Terraform workspaces may mean "environments" here — always check if workspaces are in use before assuming directory = environment.
- **Legacy resources:** Infrastructure repos often contain resources that were manually created and later imported — `terraform state list` is more authoritative than the code.
- **Helm dependency charts:** `charts/` directory may contain vendored chart dependencies — do not modify them directly.
- **Sensitive outputs:** Terraform outputs can contain secrets — never log or record `terraform output` values.

---

## Good first milestone after bootstrap

**Milestone 2 — Document environment topology and module dependency graph**

Scope:
- Map all environments (dev, staging, prod) and their state backends
- List all local modules and their callers
- Record external dependencies (registry modules, provider versions)
- Update `docs/ai/REPO_MAP.md` with IaC-specific structure
- Update `artifacts/ai/repo_discovery.json` with infrastructure details

Why this milestone: Infrastructure repos are high-risk. A clear topology map prevents accidental changes to the wrong environment and gives future agents a safe foundation.
