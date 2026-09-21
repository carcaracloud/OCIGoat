# SCN-REGISTRY-001: Public Container Repository Exposure

**Category:** container-registry | **Difficulty:** easy

## Objective

A container repository was made public to share one image by direct
link. The team believes nobody can find it without already knowing the
exact path. Confirm whether that's true.

You don't need any OCI credentials to complete this. Everything is
reachable with `docker pull` or a plain HTTP client.

## Prerequisites

- Terraform >= 1.5.0
- A compartment OCID you're authorized to deploy into
- `docker`, or `curl` and `python3` if you'd rather talk to the
  Registry HTTP API directly
- An OCI Auth Token (Console: Profile > User Settings > Tokens and
  Keys > Auth Tokens) to push the fixture image after deploy, since
  Terraform doesn't manage image content

## Deploy

```bash
cd terraform
terraform init
terraform apply -var="compartment_id=<your-compartment-ocid>"
```

Then push any small image to the repository the output names, using
your own credentials:

```bash
docker login <region>.ocir.io -u '<namespace>/<your-username>'
docker tag some-small-image <region>.ocir.io/<namespace>/ocigoat-scn-registry-001-repo:latest
docker push <region>.ocir.io/<namespace>/ocigoat-scn-registry-001-repo:latest
```

Region key examples: `phx` (Phoenix), `iad` (Ashburn), `gru` (São
Paulo), `fra` (Frankfurt), `lhr` (London). The pattern is your region's
nearest airport code.

## Where to start

- `terraform output repository_name` gives you the repository name;
  your tenancy's Object Storage namespace is your OCIR namespace too.
- Try pulling the image with no OCI credentials configured at all, from
  a different machine or a fresh Docker config if you can.
- If you'd rather not use Docker, the Registry HTTP API V2 works with
  plain `curl`: request a token from
  `https://<region>.ocir.io/20180419/docker/token?service=<region>.ocir.io&scope=repository:<namespace>/<repo>:pull`
  with no credentials at all, then use that token as a Bearer token
  against `/v2/<namespace>/<repo>/manifests/<tag>`.
- Compare what you get back to what `is_public` in `main.tf` is set to.

## Cleanup

```bash
terraform destroy
```

Verify independently that the repository is really gone, not just that
the command exited cleanly. See `manifest.yml` for the resources this
scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
