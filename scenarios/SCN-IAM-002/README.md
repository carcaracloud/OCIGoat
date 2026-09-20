# SCN-IAM-002: Cross-Resource-Type Group Membership Escalation

**Category:** iam | **Difficulty:** easy

## Objective

You've been handed credentials for a low privilege test user. The
policy attached to this user's group looks narrow: two `use` level
statements, nothing at `manage`. Find out what the combination actually
lets you do, starting from nothing but the credential you're given.

## Prerequisites

- OCI CLI configured (`oci setup config`)
- Terraform >= 1.5.0
- A tenancy OCID you're authorized to deploy into
- An RSA keypair generated specifically for the test user: `openssl
  genrsa -out test-operator.pem 2048 && openssl rsa -pubout -in
  test-operator.pem -out test-operator_public.pem`

## Deploy

```bash
cd terraform
terraform init
terraform apply \
  -var="tenancy_ocid=<your-tenancy-ocid>" \
  -var="test_user_email=<any-unique-email>" \
  -var="test_user_api_public_key=$(cat test-operator_public.pem)"
```

## Where to start

- `terraform output` gives you the test user's OCID, its API key
  fingerprint, and the OCID of a second group. Set up a CLI profile for
  the test user with these plus your tenancy OCID and the private key
  you generated.
- Read the test user's policy carefully. Two verbs, two different
  resource-types. Neither one alone does much.
- The second group has its own policy, with a capability the test user
  doesn't start with. You don't need to touch that policy directly.
- You don't need SSH, a second credential, or anything outside the
  Identity service to complete this.

## Cleanup

```bash
terraform destroy
```

Verify independently that nothing survived. See `manifest.yml` for the
resources this scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
