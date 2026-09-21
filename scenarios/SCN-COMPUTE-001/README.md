# SCN-COMPUTE-001: Custom Image Export Combined with a Pre-Authenticated Request

**Category:** compute, storage | **Difficulty:** medium

## Objective

You've been handed a credential that can manage instances and manage
objects in a compartment, two verbs that sound like routine operational
access. There's a running instance in the compartment and an empty
bucket next to it. Find out what those two verbs let you do together
that neither lets you do alone.

## Prerequisites

- OCI CLI configured (`oci setup config`)
- Terraform >= 1.5.0
- A compartment OCID you're authorized to deploy into
- `curl`

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
  fingerprint, the source instance's OCID, and the bucket's name and
  namespace. Set up a CLI profile for the test user.
- Check `main.tf` for the two statements in the test user's policy.
  Neither one mentions images, exports, or pre-authenticated requests
  by name.
- Turn the running instance into a custom image, export that image to
  the bucket, then create a pre-authenticated request over the
  exported object. Three CLI calls, same credential the whole way.
- `oci compute image export to-object` doesn't take a `--wait-for-state`
  flag. Poll the bucket for the object instead.
- Test the pre-authenticated request URL with a plain `curl`, from
  somewhere with no OCI credential configured at all.

## Cleanup

The image export writes the destination object as a multipart upload.
Deleting the finished object does not close that upload out, and
`terraform destroy` on the bucket will fail with `BucketNotEmpty` until
you do:

```bash
oci os multipart list --namespace <namespace> --bucket-name <bucket>
oci os multipart abort --namespace <namespace> --bucket-name <bucket> \
  --object-name <object> --upload-id <upload-id>
```

Then delete the pre-authenticated request, the exported object, and the
custom image (all via CLI, none of them are Terraform resources), and
run:

```bash
terraform destroy
```

Verify independently that everything is gone, including the test
user's Identity resources. See `manifest.yml` for the resources this
scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
