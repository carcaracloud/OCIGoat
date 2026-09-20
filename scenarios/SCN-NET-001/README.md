# SCN-NET-001: Public Service Exposure

**Category:** network | **Difficulty:** easy

## Objective

A small HTTP service was deployed in a private-looking network setup. The
team believes it's locked down. Confirm whether it's actually reachable
from the internet, and figure out why.

You don't need SSH access to complete this. Everything you need is visible
from outside the network.

## Prerequisites

- OCI CLI configured (`oci setup config`)
- Terraform >= 1.5.0
- A compartment OCID you're authorized to deploy into
- An SSH public key (used for admin access to the instance if you need it,
  not required to complete the objective)

## Deploy

```bash
cd terraform
terraform init
terraform apply \
  -var="compartment_id=<your-compartment-ocid>" \
  -var="operator_ssh_public_key=$(cat ~/.ssh/id_ed25519.pub)"
```

Wait for the instance to finish booting (a minute or two) before testing
anything. `terraform apply` finishing doesn't mean the service inside the
instance is ready.

## Where to start

- `terraform output test_service_url` gives you a URL. Try it.
- Look at what network resources actually got created. There's more than
  one layer of firewalling involved, and they don't necessarily agree with
  each other.
- The OCI CLI (`oci network security-list get`, `oci network nsg rules
  list`, ...) tells you the ground truth. Don't just trust what you'd
  expect from the resource names.

## Cleanup

```bash
terraform destroy
```

Verify independently that nothing survived. Don't just trust the exit
code. See `manifest.yml` for the resources this scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
