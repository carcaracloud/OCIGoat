# SCN-REGISTRY-002: Secret Embedded in a Public Container Image Layer

**Category:** container-registry | **Difficulty:** easy

## Objective

A repository is public. The team believes that's fine, because the
final image doesn't expose anything sensitive, whatever showed up
during the build got cleaned up in a later step. Confirm whether
"cleaned up" means "gone."

## Prerequisites

- OCI CLI configured (`oci setup config`)
- Terraform >= 1.5.0
- A compartment OCID you're authorized to deploy into
- `docker`

## Deploy

```bash
cd terraform
terraform init
terraform apply -var="compartment_id=<your-compartment-ocid>"
```

Then build and push a small fixture image with a secret written in one
layer and removed in a later one:

```dockerfile
FROM busybox
COPY credentials.txt /opt/app/config/credentials.txt
RUN rm /opt/app/config/credentials.txt
```

```bash
echo "AWS_SECRET_ACCESS_KEY=fake-not-real-AKIA1234567890EXAMPLE" > credentials.txt
docker build -t <region-key>.ocir.io/<namespace>/ocigoat-scn-registry-002-repo:latest .
docker login <region-key>.ocir.io -u '<namespace>/<your-username>'
docker push <region-key>.ocir.io/<namespace>/ocigoat-scn-registry-002-repo:latest
```

Your tenancy's Object Storage namespace is your OCIR namespace too
(`oci os ns get`). Region key is your region's nearest airport code:
`phx` (Phoenix), `iad` (Ashburn), `gru` (São Paulo), `fra` (Frankfurt),
`lhr` (London), and so on.

## Where to start

- `docker pull` the image anonymously, from a machine with no
  registry credential configured at all.
- `docker save` it, or pull the layer blobs directly via the Docker
  Registry HTTP API v2, and extract each layer separately.
- Look for `credentials.txt` in each layer, not just the final
  filesystem. `docker run` won't show it to you, look at the layers
  themselves.

## Cleanup

```bash
terraform destroy
```

Verify independently that the repository is gone. See `manifest.yml`
for the resources this scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
