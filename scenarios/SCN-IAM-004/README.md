# SCN-IAM-004: Compartment-Scoped Dynamic Group Self-Enrollment

**Category:** iam, compute | **Difficulty:** hard

## Objective

You've been handed credentials for a low privilege test user, scoped to
launch ordinary compute workloads in one compartment. There's a dynamic
group in this tenancy with a matching rule that reads:

```
instance.compartment.id = '<the same compartment your credential works in>'
```

Nobody added your test user to it. Find out if that matters.

You'll need to launch an instance yourself and connect to it to finish
this one.

## Prerequisites

- OCI CLI configured (`oci setup config`)
- Terraform >= 1.5.0
- A tenancy OCID and a compartment OCID you're authorized to deploy into
- Two RSA-family keypairs: one for the test user's API key, one
  ED25519/RSA SSH keypair for connecting to whatever instance you launch
- Enough patience for the instance to finish booting before you connect

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
  fingerprint, and a subnet OCID already wired for public access with
  SSH open. Set up a CLI profile for the test user with these plus your
  tenancy OCID and the private key you generated.
- Check what the test user's policy grants directly. It's enough to
  launch an instance, nothing more.
- Launch an instance into the subnet from the output, in the same
  compartment your credential is scoped to, with your own SSH key in
  its metadata. `VM.Standard.E2.1.Micro` is the most reliably available
  Always Free shape; `VM.Standard.A1.Flex` works too when capacity
  allows.
- Once it's running, connect to it. From inside, install `oci-cli`
  using the official installer (`curl -sL
  https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh
  | bash`) rather than a plain `pip install`, especially on a small
  shape. It resolves compatible versions on its own and won't run your
  instance out of memory.
- From inside the instance, try something with `--auth
  instance_principal` that you couldn't do as the test user directly.
  Compare the two.

## Cleanup

```bash
oci compute instance terminate --instance-id <your-instance-ocid> --force
terraform destroy
```

The instance isn't managed by Terraform. You created it, you terminate
it, independently, before or after the rest. Verify independently that
nothing survived. See `manifest.yml` for the resources this scenario
creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
