# OCIGoat

Vulnerable-by-design lab environments for Oracle Cloud Infrastructure (OCI).

Same idea as [CloudGoat](https://github.com/RhinoSecurityLabs/cloudgoat), applied
to OCI instead of AWS: Terraform builds a deliberately insecure environment,
you investigate it, you destroy it when you're done. Built for security
engineers, cloud analysts, and anyone learning offensive/defensive OCI
security.

OCIGoat is OCI-first. It is not a multi-cloud tool, and it doesn't try to be.

## Status

Early. Ten validated scenarios so far. No CLI yet, you run Terraform
directly. Treat this as a working prototype, not a finished product.

## Requirements

- [OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm),
  configured (`oci setup config`)
- [Terraform](https://developer.hashicorp.com/terraform) >= 1.5.0
- An OCI tenancy with a dedicated compartment (don't run this against your
  root compartment)

## Scenarios

| ID | Name | Category | Difficulty |
|---|---|---|---|
| [SCN-NET-001](scenarios/SCN-NET-001) | Public Service Exposure | network | easy |
| [SCN-IAM-001](scenarios/SCN-IAM-001) | Policy Rewrite Privilege Escalation | iam | easy |
| [SCN-IAM-002](scenarios/SCN-IAM-002) | Cross-Resource-Type Group Membership Escalation | iam | easy |
| [SCN-IAM-003](scenarios/SCN-IAM-003) | API Key Impersonation via Manage Users | iam | easy |
| [SCN-STORAGE-001](scenarios/SCN-STORAGE-001) | Public Bucket Listing Exposure | storage | easy |
| [SCN-IAM-004](scenarios/SCN-IAM-004) | Compartment-Scoped Dynamic Group Self-Enrollment | iam, compute | hard |
| [SCN-REGISTRY-001](scenarios/SCN-REGISTRY-001) | Public Container Repository Exposure | container-registry | easy |
| [SCN-OKE-001](scenarios/SCN-OKE-001) | Public Kubernetes API Endpoint Exposure | oke | easy |
| [SCN-DATABASE-001](scenarios/SCN-DATABASE-001) | Autonomous Database Open by Default Without an Access Control List | database | easy |
| [SCN-VAULT-001](scenarios/SCN-VAULT-001) | Compartment-Scoped Secret Policy Without Target Condition | vault | easy |

Each scenario lives in its own folder under `scenarios/`, with its own
Terraform, a player README (objective, no spoilers), and a separate
`solution/` with the full walkthrough.

## Quick start

```bash
cd scenarios/SCN-NET-001/terraform
terraform init
terraform apply \
  -var="compartment_id=<your-compartment-ocid>" \
  -var="operator_ssh_public_key=$(cat ~/.ssh/id_ed25519.pub)"
```

Read the scenario's own README before you start. When you're done:

```bash
terraform destroy
```

## Cost

Scenarios are designed to fit inside the OCI Always Free tier where
possible, but "Always Free" is not a blanket guarantee. It depends on your
region, your tenancy's usage, and what Oracle currently offers. Check the
cost notes in each scenario's `manifest.yml` before applying, and always run
`terraform destroy` when you're finished.

## Why this exists

AWS has CloudGoat, iam-vulnerable, and a handful of others. GCP has
GCP-goat and similar labs. OCI doesn't really have a maintained equivalent.
That's the gap OCIGoat is for.

## License

MIT. See [LICENSE](LICENSE).
