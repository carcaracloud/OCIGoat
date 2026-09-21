# SCN-DATABASE-001: Autonomous Database Open by Default Without an Access Control List

**Category:** database | **Difficulty:** easy

## Objective

A database was provisioned in a hurry. Nobody configured an access
control list yet, the plan was to "do it later, before anything real
goes in it." Find out whether that plan already failed.

You don't need any database credential to complete this. Everything is
reachable with `curl` and the OCI CLI.

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
  -var="compartment_id=<your-compartment-ocid>" \
  -var="admin_password=<a-password-you-will-never-use>"
```

Check that Always Free Autonomous Database is available in your home
region before you apply, rather than assuming it. If it isn't, `apply`
will fail on that specific point, not silently do something else.

## Where to start

- `terraform output connection_urls` gives you a list of HTTPS URLs for
  the database's built-in web tools.
- Pick any one of them and hit it with `curl`, from your own machine,
  with no credential, no wallet, no VPN.
- Look at what comes back. You don't need to log in to learn something
  here.
- Check `main.tf` for what actually controls this, and what argument
  was never set.

## Cleanup

```bash
terraform destroy
```

Verify independently that the database is really gone, not just that
the command exited cleanly. See `manifest.yml` for the resources this
scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
