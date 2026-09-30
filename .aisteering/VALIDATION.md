# Tailnet deployment validation

Configuration-only scope: render and lint the upstream Helm chart with deploy/tailnet/values.yaml and the non-secret owner.yaml, then use kubectl server dry-run against context tailscale-operator.tailc69d48.ts.net, namespace buzz. Confirm rendered workloads use the intended secret, image, ports and storage class. No application API is changed.

Live validation: wait for ExternalSecret Ready, all deployments/StatefulSets ready and PVCs Bound; verify HTTPS NIP-11 metadata and WebSocket authentication over buzz.tailc69d48.ts.net; exercise signed owner event publication and retrieval. Record exact source/image and observed evidence under .aisteering/evidence/.

Agent Steering bootstrap skill installation is blocked by preserved upstream-tracked skill symlinks; see the dated scratchpad. Do not rely on installed project guidance or report doctor success.

CI/local contract command: `python -m unittest discover -s deploy/tailnet/tests -v`
with Helm 3.20.0 on PATH and PyYAML 6.0.2.
