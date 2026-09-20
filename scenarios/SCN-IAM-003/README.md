# SCN-IAM-003: API Key Impersonation via Manage Users

**Category:** iam | **Difficulty:** easy

## Objective

You've been handed credentials for a low privilege test user. Its group
has one statement: `manage users`. That sounds like routine account
administration. There's a second user in this tenancy with more access
than you have. Find out if you can act as them, without ever knowing
their password.

## Prerequisites

- OCI CLI configured (`oci setup config`)
- Terraform >= 1.5.0
- A tenancy OCID you're authorized to deploy into
- Two RSA keypairs: one for the test user, one you'll use later in the
  exercise. `openssl genrsa -out test-operator.pem 2048 && openssl rsa
  -pubout -in test-operator.pem -out test-operator_public.pem`, then the
  same again with a different filename.

## Deploy

```bash
cd terraform
terraform init
terraform apply \
  -var="tenancy_ocid=<your-tenancy-ocid>" \
  -var="test_user_email=<any-unique-email>" \
  -var="target_admin_email=<any-other-unique-email>" \
  -var="test_user_api_public_key=$(cat test-operator_public.pem)"
```

## Where to start

- `terraform output` gives you the test user's OCID, its API key
  fingerprint, and the OCID of a second user in the tenancy. Set up a
  CLI profile for the test user with these plus your tenancy OCID and
  the private key you generated.
- Read what the test user's policy actually grants. `manage users`
  sounds like it's about editing accounts. Check what operations that
  verb covers for the `users` resource-type specifically, not what the
  name suggests.
- You have a second keypair. Think about what you could do with it and
  the permission you already have, targeting the other user's OCID.
- You don't need SSH or anything outside the Identity service to
  complete this.

## Cleanup

```bash
terraform destroy
```

Verify independently that nothing survived. See `manifest.yml` for the
resources this scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
