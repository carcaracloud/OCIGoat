# SCN-ORM-001: Resource Manager Stack State Exposed by Read-Only Access

**Category:** resource-manager | **Difficulty:** easy

## Objective

You've been handed credentials for a low privilege test user. Its
group has one statement: `read orm-stacks`. That sounds like
"look at stack metadata," nothing more. There's a stack in this
compartment that was applied for real and computed a value nobody
meant to hand out. Find out if `read` gets you there anyway.

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

This scenario's Terraform only creates the test user and its policy.
The target stack itself has to be created separately, because
`oci_resourcemanager_stack` only exists as a Terraform data source in
the `oracle/oci` provider, not a resource. Create a minimal config with
a value Terraform computes on its own, so nothing beyond this lab's own
setup ever touches it:

```hcl
# main.tf
terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "3.6.3"
    }
  }
}

resource "random_password" "admin" {
  length  = 20
  special = true
}
```

```bash
zip stack-config.zip main.tf

STACK_ID=$(oci resource-manager stack create \
  --compartment-id <your-compartment-ocid> \
  --config-source stack-config.zip \
  --display-name "target-stack" \
  --terraform-version "1.5.x" \
  --query 'data.id' --raw-output)

oci resource-manager job create-apply-job \
  --stack-id "$STACK_ID" \
  --execution-plan-strategy AUTO_APPROVED \
  --wait-for-state SUCCEEDED --wait-for-state FAILED
```

## Where to start

- `terraform output` gives you the test user's OCID and API key
  fingerprint. Set up a CLI profile for it.
- Note the stack's OCID from the step above.
- Read what `read orm-stacks` actually covers. Don't assume "read"
  means "metadata only," check the verb table.
- Pull the stack's Terraform state using only the test user's
  credential, and look for what the `random_password` resource
  computed.

## Cleanup

```bash
oci resource-manager job create-destroy-job --stack-id "$STACK_ID" --execution-plan-strategy AUTO_APPROVED --wait-for-state SUCCEEDED --wait-for-state FAILED
oci resource-manager stack delete --stack-id "$STACK_ID" --force
terraform destroy
```

Verify independently that both the stack and the test user are gone.
See `manifest.yml` for the resources this scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
