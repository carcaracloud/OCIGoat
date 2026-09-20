# SCN-STORAGE-001: Public Bucket Listing Exposure

**Category:** storage | **Difficulty:** easy

## Objective

A bucket was made public so a specific file could be shared by link. The
team believes nobody can find anything in it without already having that
link. Confirm whether that's true.

You don't need any OCI credentials to complete this. Everything is
reachable with a plain HTTP client.

## Prerequisites

- Terraform >= 1.5.0
- A compartment OCID you're authorized to deploy into
- `curl` or a browser

## Deploy

```bash
cd terraform
terraform init
terraform apply \
  -var="compartment_id=<your-compartment-ocid>" \
  -var="region=<your-region, e.g. us-ashburn-1>"
```

## Where to start

- `terraform output listing_url` gives you a URL. Try it with `curl`,
  no headers, no credentials.
- `terraform output object_url` gives you another one. Try that too.
- Compare what each one returns to what `access_type` in `main.tf` is
  actually set to versus what the two public options for that field are
  named.

## Cleanup

```bash
terraform destroy
```

Verify independently that the bucket is really gone, not just that the
command exited cleanly. See `manifest.yml` for the resources this
scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
