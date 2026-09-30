# Project Authority Map

Status: partial — upstream skill paths prevent managed Agent Steering hydration.

## Repository

- Provider: GitHub
- Canonical upstream: https://github.com/block/buzz
- Deployment fork: https://github.com/igor-im/buzz
- Integration branch: main
- Resolve integrated code from the fork main branch, not the local feature branch.

## Task tracker

This requested installation is tracked in `.aisteering/summaries/2026-09-29-tailnet.md`.
No external issue tracker has been selected for ongoing fork maintenance.

## Authority chain

| Question | Authoritative source | How to resolve it |
| --- | --- | --- |
| What architecture is intended? | VISION.md, VISION_SOVEREIGN.md, ARCHITECTURE.md | Read upstream product and runtime contracts. |
| How is Buzz built? | Dockerfile, .github/workflows/docker.yml | Match source commit to the pinned published image. |
| How is this installation deployed? | deploy/tailnet/README.md | Use the explicit Helm and kubectl context/namespace commands. |
| What is running? | Named Kubernetes context, buzz namespace | Query current resources, Helm release and image IDs. |
| What has worked? | .aisteering/evidence/ | Read timestamped real scenario results. |
| What should the next agent do? | .aisteering/summaries/ and relevant scratchpads | Reconcile evidence with current runtime and fork PR state. |

Managed bootstrap remains incomplete. Preserve upstream-tracked skill paths; do
not overwrite them to force hydration. No architecture maturity promotion or
production-readiness approval is claimed by this installation.
