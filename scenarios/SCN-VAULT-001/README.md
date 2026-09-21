# SCN-VAULT-001: Compartment-Scoped Secret Policy Without Target Condition

**Category:** vault | **Difficulty:** easy

## Objective

You've been handed credentials for a low privilege test user. Its group
has one statement: `read secret-family` in a compartment. Someone meant
that to cover exactly one secret. There's a second secret in the same
compartment that was never supposed to be part of the deal. Find out if
it is anyway.

## Prerequisites

- OCI CLI configured (`oci setup config`)
- Terraform >= 1.5.0
- A tenancy OCID you're authorized to deploy into
- An RSA keypair for the test user: `openssl genrsa -out
  test-operator.pem 2048 && openssl rsa -pubout -in test-operator.pem
  -out test-operator_public.pem`

## Deploy

```bash
cd terraform
terraform init
terraform apply \
  -var="tenancy_ocid=<your-tenancy-ocid>" \
  -var="compartment_id=<your-compartment-ocid>" \
  -var="test_user_email=<any-unique-email>" \
  -var="test_user_api_public_key=$(cat test-operator_public.pem)"
```

## Where to start

- `terraform output` gives you the test user's OCID, its API key
  fingerprint, and two secret OCIDs. Set up a CLI profile for the test
  user with these plus your tenancy OCID and the private key you
  generated.
- Read what the test user's policy actually grants, and what it's
  scoped by. Compare that to what condition variables exist for
  scoping a Vault/Secrets policy to one specific secret.
- You have two secret OCIDs. Try reading both with the test user's
  credential, not just the one you'd guess was "intended."
- You don't need anything outside Vault/Secrets and Identity to
  complete this.

## Cleanup

```bash
terraform destroy
```

Verify independently that nothing survived, including the vault itself
(vaults go through a scheduled deletion window rather than disappearing
immediately). See `manifest.yml` for the resources this scenario
creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
