# SCN-IAM-001: Policy Rewrite Privilege Escalation

**Category:** iam | **Difficulty:** easy

## Objective

You've been handed credentials for a low privilege test user. The team
believes this user can only manage policy documents, nothing else. Find
out what this user can actually do with that access, starting from
nothing but the credential you're given.

## Prerequisites

- OCI CLI configured (`oci setup config`)
- Terraform >= 1.5.0
- A tenancy OCID you're authorized to deploy into
- An RSA keypair generated specifically for the test user (not your own
  admin key): `openssl genrsa -out test-operator.pem 2048 && openssl rsa
  -pubout -in test-operator.pem -out test-operator_public.pem`

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

- `terraform output` gives you the test user's OCID and API key
  fingerprint. Set up a second OCI CLI profile with these, your own
  tenancy OCID, and the private key half of the pair you generated.
- Try a few basic `oci iam` reads with that profile. Most will fail.
- `terraform output policy_ocid` and `oci iam policy get` show you
  exactly what the test user's group is allowed to do. Read it
  carefully; the scope is narrower than it might look at first glance.
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
