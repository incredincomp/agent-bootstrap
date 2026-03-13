# Example Notes: Kubernetes Platform Repository

This document guides an agent performing discovery or bootstrap on a Kubernetes platform or cluster-configuration repository.

---

## Likely repository characteristics

- Primary content: Kubernetes manifests (YAML), Helm charts, Kustomize overlays, or a mix
- Languages: YAML (dominant), Go (for operators/controllers), Python or Shell (for scripts/tooling)
- Tools: `kubectl`, `helm`, `kustomize`, `flux` or `argocd` (GitOps), `kubeconform`, `kubeval`, `conftest`
- Package management: Helm chart dependencies (`Chart.yaml` + `charts/`), Kustomize remote bases
- GitOps model: Many platform repos use Flux or Argo CD — the repo state IS the cluster state
- CI/CD: Validation pipelines (`helm lint`, `kubeconform`, OPA policy checks); deployment via GitOps sync or CI apply
- Common structure:
  - `clusters/` or `environments/` — per-cluster or per-environment configuration
  - `apps/` or `workloads/` — application deployment manifests
  - `infrastructure/` — core cluster components (cert-manager, ingress, monitoring)
  - `charts/` — custom Helm charts
  - `scripts/` — bootstrap, rotation, and operational scripts
  - `docs/` — runbooks, architecture, on-call guides

---

## What an agent should prioritize in discovery

1. **GitOps controller:** Is Flux or Argo CD in use? If yes, the reconciliation model means changes to the repo are automatically applied to the cluster. **Understand this before touching anything.**
2. **Cluster topology:** How many clusters? Are they separated by directory, by branch, or by Kustomize overlay? Map this before making recommendations.
3. **Namespace strategy:** How are namespaces organized? Tenant-per-namespace, team-per-namespace, or functional grouping?
4. **Secrets management:** Look for `SealedSecret`, `ExternalSecret`, SOPS-encrypted files, or Vault integration. Identify which secrets approach is in use — this constrains how secrets can be modified.
5. **RBAC configuration:** ClusterRole, ClusterRoleBinding, Role, RoleBinding files — these are high-risk. Note their presence.
6. **Admission webhooks / policies:** Check for OPA Gatekeeper, Kyverno, or Pod Security Admission — these policies constrain what can be deployed.
7. **Helm releases vs. raw manifests:** Some repos mix Helm releases (via Flux HelmRelease or Argo Application) with raw manifests — identify which is which before editing.

---

## Typical authoritative files

| File | Why authoritative |
|------|------------------|
| `clusters/<name>/flux-system/` | Flux bootstrap — do not modify without understanding Flux reconciliation |
| `Chart.yaml` | Helm chart metadata and dependencies |
| `values.yaml` / `values-*.yaml` | Helm release configuration per environment |
| `kustomization.yaml` | Kustomize overlay entry point |
| `gotk-components.yaml` | Flux Toolkit component definitions (generated — do not edit directly) |
| `scripts/bootstrap.sh` | Cluster bootstrapping procedure |

---

## Common traps

- **GitOps means live:** In a GitOps model, merging to main may immediately apply changes to a production cluster. Never push without understanding the sync policy.
- **Sealed secrets are encrypted per-cluster:** A `SealedSecret` encrypted for cluster A cannot be used on cluster B. Do not copy sealed secrets between clusters.
- **Helm chart vendoring:** The `charts/` subdirectory of a Helm chart may be vendored dependencies — do not edit vendored charts directly; update `Chart.yaml` and re-run `helm dependency update`.
- **Kustomize remote bases:** `kustomization.yaml` may reference remote bases (GitHub URLs) — the remote version may differ from what is documented. Always check the pinned version.
- **CRD ordering:** Custom Resource Definitions must be applied before Custom Resources. Apply ordering matters in non-GitOps workflows.
- **`kubectl apply` is not idempotent for all resources:** Some resources (notably `Job`, `HorizontalPodAutoscaler`) have apply semantics that require care.
- **Cluster-scoped vs. namespace-scoped:** ClusterRole, ClusterRoleBinding, PersistentVolume, and Namespace resources are cluster-scoped — changes affect the entire cluster, not just one namespace.

---

## Good first milestone after bootstrap

**Milestone 2 — Document cluster topology and GitOps reconciliation model**

Scope:
- Identify all clusters and their environments (dev, staging, prod)
- Map the GitOps sync model (Flux Kustomizations or Argo Applications) and sync intervals
- Identify the secrets management approach
- Identify all admission policies in place
- Record findings in `docs/ai/REPO_MAP.md` and `artifacts/ai/repo_discovery.json`

Why this milestone: Kubernetes platform repos have the highest blast radius of any repo type. A thorough topology and policy map is a prerequisite for any safe change. It also gives on-call engineers a fast reference.
