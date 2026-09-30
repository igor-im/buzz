# Architecture maturity and work modes

## Purpose

Architecture maturity records accumulated evidence for one architecture or capability. Work mode controls how the current task proceeds. Delivery state is separate from both: a branch can be merged or deployed while its architecture remains an unproved hypothesis.

The managed `architecture-promotion` skill owns the current gate rubrics, mode classification, and mode-specific implementation guidance. This project owns its approved architecture, named plans, promotion records, validation evidence, and authority configuration.

## Architecture maturity

| Maturity | Meaning |
| --- | --- |
| `hypothesis` | A falsifiable architectural claim and its thin scenario are recorded. |
| `scenario-proven` | One timestamped passing evidence record proves the whole scenario through every required real seam. |
| `production-approved` | The scenario remains proved and security, failure behavior, migration, rollback, and observability are resolved. |

Maturity is monotonic: `hypothesis` → `scenario-proven` → `production-approved`. Git, work mode, task tracker, build, deployment, and runtime state do not promote it.

## Work modes

| Mode | Meaning |
| --- | --- |
| `exploration` | Understand the problem, compare approaches, define claims, or analyze readiness. |
| `experimentation` | Test a falsifiable claim through the smallest required real scenario and record the result. |
| `production` | Make a production-approved result dependable and safe to operate under project authorities. |
| `vibe-engineering` | Work free-wheeling and feedback-first from broad intent while keeping irreversible and production boundaries explicit. |

Modes are not ranks and may change without changing maturity. No mode history is a maturity gate: experimentation is selected only when the current task is an experiment, and a scenario-proven architecture may use it again. Vibe-engineered work may be committed and reviewed, but must transition to production mode before deployment or critical-system dependence. Production mode requires `production-approved` maturity.

## Promotion record

Create one Markdown file per architecture under `.aisteering/architecture/`. Its YAML frontmatter must follow schema version 2:

```yaml
---
schemaVersion: 2
architectureId: orders-v2
maturity: hypothesis
architectureRefs:
  - .aisteering/adrs/001-orders-v2.md
hypothesis: A transactional outbox prevents accepted orders from losing their dispatch event.
thinScenario:
  id: accept-and-dispatch-order
  description: Accept one real order, persist it, publish its event, and observe dispatch.
  requiredRealSeams:
    - http-ingress
    - postgres-write
    - broker-publish
    - worker-consume
  allowedSubstitutions:
    - payment-sandbox
  evidence: []
productionReadiness:
  security:
    status: unresolved
  failureBehavior:
    status: unresolved
  migration:
    status: unresolved
  rollback:
    status: unresolved
  observability:
    status: unresolved
---
```

Use a falsifiable `hypothesis`. `requiredRealSeams` names boundaries that evidence must actually traverse. `allowedSubstitutions` may name substitutes only for non-required dependencies.

Each production-readiness gate has one disposition:

- `status: unresolved`
- `status: satisfied` plus a non-empty `evidence` list of project-relative paths
- `status: not-applicable` plus a project-specific `reason`

Old schema-version-1 records are not silently translated. Rewrite `experiment` to `hypothesis` when no qualifying passing evidence exists or to `scenario-proven` when it does; rewrite `slice-proven` to `scenario-proven`; then set `schemaVersion: 2`.

## Validation evidence

Store one timestamped Markdown record per real scenario run under `.aisteering/evidence/`. Evidence records remain schema version 1:

```yaml
---
schemaVersion: 1
evidenceId: orders-v2-scenario-20260829
architectureId: orders-v2
scenarioId: accept-and-dispatch-order
recordedAt: 2026-08-29T19:30:00-05:00
sourceCommit: 0123456789abcdef0123456789abcdef01234567
environment: staging/orders-v2-proof
procedure: Run scripts/validate-orders-v2.sh against the named staging deployment.
result: passed
resultSummary: The accepted order was persisted, published, consumed, and marked dispatched.
realSeams:
  - http-ingress
  - postgres-write
  - broker-publish
  - worker-consume
substitutions:
  - payment-sandbox
---
```

Record observed results only. A plan, unit test, mocked interaction, build, merge, or deployment is not proof unless it actually runs the named scenario through every required real seam.

## Mechanical checks and transitions

Check current declared maturity independently:

```bash
agent-steering architecture check \
  --project <absolute-project-root> \
  --record <project-relative-promotion-record> \
  --required-maturity <hypothesis|scenario-proven|production-approved>
```

Preview both explicit transition axes without writing:

```bash
agent-steering architecture transition \
  --project <absolute-project-root> \
  --record <project-relative-promotion-record> \
  --to <hypothesis|scenario-proven|production-approved> \
  --mode <exploration|experimentation|production|vibe-engineering>
```

An ineligible result stops before installation planning. Apply an eligible reviewed transition with the same arguments plus `--apply`. The operation activates the exact locked work-mode profile from portable project state, requires doctor to return zero findings, refreshes evidence, and updates only a needed maturity scalar. A same-maturity mode change leaves the promotion record unchanged. It does not derive catalog, cache, source, target, or provider inputs from the plan and does not create another lock or state format.
