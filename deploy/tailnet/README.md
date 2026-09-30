# Buzz on the tailnet

Status: runtime removed at the user's request on 2026-09-29 (America/Chicago).
The Helm release, standalone MinIO workload, ExternalSecret, runtime Secret,
Ingress and Tailscale proxy are gone. The namespace and four PVCs remain for
recovery, along with local app data and 1Password items. The addresses below
are historical; the reproduction commands would reinstall the service.
See `.aisteering/summaries/2026-09-29-removal.md` for verification and the
remaining local package removal step.

This application-owned configuration deploys Buzz into namespace `buzz` on
Kubernetes context `tailscale-operator.tailc69d48.ts.net`.

- Browser/repository UI: https://buzz.tailc69d48.ts.net
- Desktop/mobile/CLI relay: wss://buzz.tailc69d48.ts.net
- Owner private key: 1Password `infra/buzz-owner/BUZZ_PRIVATE_KEY`.
- Service credentials: 1Password `infra/app-buzz`, synchronized by External Secrets.

Use the Buzz desktop/mobile client for chat. The bundled browser UI is the
repository browser, not the full desktop chat client. Import the owner key from
1Password in the client; never put it in chat, Git, command arguments or logs.
`owner.yaml` contains the public key only. The owner key is not mounted in any pod.

## Reproduce

Requires Helm 3, kubectl, access to the named Kubernetes context and the existing
`onepassword` ClusterSecretStore. Run from the repository root:

```sh
helm dependency build deploy/charts/buzz
helm lint deploy/charts/buzz -f deploy/tailnet/values.yaml -f deploy/tailnet/owner.yaml
helm template buzz deploy/charts/buzz --namespace buzz \
  -f deploy/tailnet/values.yaml -f deploy/tailnet/owner.yaml > /tmp/buzz-rendered.yaml
kubectl --context tailscale-operator.tailc69d48.ts.net create namespace buzz --dry-run=client -o yaml |
  kubectl --context tailscale-operator.tailc69d48.ts.net apply -f -
kubectl --context tailscale-operator.tailc69d48.ts.net -n buzz apply --dry-run=server \
  -f deploy/tailnet/platform.yaml -f /tmp/buzz-rendered.yaml
kubectl --context tailscale-operator.tailc69d48.ts.net -n buzz apply -f deploy/tailnet/platform.yaml
kubectl --context tailscale-operator.tailc69d48.ts.net -n buzz wait \
  externalsecret/buzz-runtime --for=condition=Ready --timeout=120s
helm upgrade --install buzz deploy/charts/buzz \
  --kube-context tailscale-operator.tailc69d48.ts.net --namespace buzz \
  -f deploy/tailnet/values.yaml -f deploy/tailnet/owner.yaml --wait --timeout 10m
```

No Terraform or tailnet ACL mutation is required: the existing Tailscale
operator publishes the Ingress using the current `tag:k8s` access policy.
Application authentication and relay membership remain required. Dependencies
are ClusterIP-only. No Funnel or public ingress is configured.

## Storage and availability

One relay, PostgreSQL, Redis and MinIO instance each. Ceph RBD holds PostgreSQL
(10 GiB), Redis (4 GiB), and object storage (10 GiB). Git working directories are
explicitly ephemeral; authoritative Git/media objects live in MinIO and Postgres.
This installation is not highly available and has no app-specific backup schedule.

Redis is explicitly placed on `control-plane-1`: its initial Ceph mount on
`worker-general-1` stalled. Remove this placement only after validating storage
on the intended node. This does not repair the shared worker's storage plugin. Redis uses the explicit
`buzz-redis-data` claim. The unused original `data-buzz-redis-0` claim is retained:
automatic approval review rejected destructive PVC cleanup.

Images are immutable. The relay amd64 digest corresponds to upstream source
`12670bd0f037c66a682272bb81c46c3f254fad74`. MinIO uses the upstream Buzz project's
published amd64 CI image, pinned by digest, containing the official MinIO and mc
release binaries with checksums specified in `.github/ci/minio/Dockerfile`.
Upstream Quay image pulls returned 401; the substituted registry/image is
explicit in both manifests. The upstream calls this image CI-only; its use here
is for this single-instance installation and is not a production support claim.

## Inspect and recover

```sh
kubectl --context tailscale-operator.tailc69d48.ts.net -n buzz get pods,pvc,externalsecret,ingress
kubectl --context tailscale-operator.tailc69d48.ts.net -n buzz logs deployment/buzz -c relay --tail=100
curl --fail --header 'Accept: application/nostr+json' https://buzz.tailc69d48.ts.net
helm history buzz --kube-context tailscale-operator.tailc69d48.ts.net --namespace buzz
```

Helm manages the relay and database/cache charts. `platform.yaml` is applied
separately and owns the namespace, ExternalSecret, MinIO, its PVC and ingress.
Changes to platform.yaml must be reviewed and applied alongside Helm changes.
Do not delete the namespace or PVCs to roll back: the Ceph storage class has a
Delete reclaim policy. Helm rollback alone does not reverse database migrations;
inspect upstream migration compatibility and take a verified backup first.

## Automated contract checks

The pull-request workflow runs Helm lint and these four deterministic checks:

```sh
python -m pip install PyYAML==6.0.2
python -m unittest discover -s deploy/tailnet/tests -v
```

See `.aisteering/evidence/2026-09-29-tailnet.md` for the authenticated live scenario.
