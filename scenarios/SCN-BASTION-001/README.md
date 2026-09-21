# SCN-BASTION-001: Bastion Session Allowlist Open to Any Client IP

**Category:** bastion | **Difficulty:** medium

## Objective

An instance with no public IP sits behind a Bastion. The team treats
that as the access control. You've been handed credentials that can
create a Bastion session, from your own ordinary internet connection,
nothing corporate or pre-approved about it. Find out whether that's
enough.

## Prerequisites

- OCI CLI configured (`oci setup config`)
- Terraform >= 1.5.0
- A tenancy OCID you're authorized to deploy into
- Two SSH keypairs: one you'll use for the Bastion session tunnel
  itself, one already authorized on the target
  (`ssh-keygen -t ed25519 -f session-key -N ''` for the first; the
  second is the `target_ssh_public_key` you pass to Terraform)

## Deploy

```bash
cd terraform
terraform init
terraform apply \
  -var="tenancy_ocid=<your-tenancy-ocid>" \
  -var="compartment_id=<your-compartment-ocid>" \
  -var="test_user_email=<any-unique-email>" \
  -var="test_user_api_public_key=$(cat test-operator_public.pem)" \
  -var="target_ssh_public_key=$(cat target-key.pub)"
```

## Where to start

- `terraform output` gives you the test user's OCID, its API key
  fingerprint, the Bastion's OCID, and the target's private IP. Set up
  a CLI profile for the test user.
- Check `main.tf` for what `client_cidr_block_allow_list` is set to on
  the Bastion, and think about what that value actually restricts.
- Create a port forwarding session from wherever you're sitting right
  now, no VPN, no special network. Tunnel it, then SSH through the
  tunnel to the target using the key you had authorized there.
- The interesting question isn't whether you have permission to create
  a session. You do; that's given. It's whether the Bastion itself
  cared where you were creating it from.

## Cleanup

```bash
terraform destroy
```

Verify independently that everything is gone, including the test
user's Identity resources. See `manifest.yml` for the resources this
scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
