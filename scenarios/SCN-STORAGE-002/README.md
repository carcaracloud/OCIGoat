# SCN-STORAGE-002: Backup Bucket Without Versioning or Retention Rules

**Category:** storage | **Difficulty:** easy

## Objective

A bucket named for nightly backups holds exactly one object. You've
been handed credentials for a test user with routine write access to
it, the kind of access a backup job itself would need. Find out what
actually stands between that access and permanently losing what's in
there.

## Prerequisites

- OCI CLI configured (`oci setup config`)
- Terraform >= 1.5.0
- A tenancy OCID you're authorized to deploy into

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

- `terraform output` gives you the bucket name, the object name, the
  test user's OCID, and its API key fingerprint. Set up a CLI profile
  for the test user.
- Check `main.tf` for what's configured on the bucket, and, just as
  importantly, what isn't.
- Read the object's current content, then overwrite it using the test
  user's access. Read it again.
- Try to find the original content some other way. The bucket's name
  suggests it should still be there in some form.

## Cleanup

```bash
terraform destroy
```

Verify independently that everything is gone. See `manifest.yml` for
the resources this scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
