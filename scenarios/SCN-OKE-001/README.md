# SCN-OKE-001: Public Kubernetes API Endpoint Exposure

**Category:** oke | **Difficulty:** easy

## Objective

A Kubernetes cluster's worker nodes were deliberately kept off the
public internet. The team believes this makes the cluster private.
Confirm whether the control plane agrees.

You don't need a kubeconfig or any cluster credential to complete this.

## Prerequisites

- OCI CLI configured (`oci setup config`), used only to find a
  supported Kubernetes version before deploying
- Terraform >= 1.5.0
- A compartment OCID you're authorized to deploy into
- `curl`

## Deploy

Check which Kubernetes versions are currently supported before you
apply, rather than assuming one:

```bash
oci ce cluster-options get --cluster-option-id all --query 'data."kubernetes-versions"'
```

```bash
cd terraform
terraform init
terraform apply \
  -var="compartment_id=<your-compartment-ocid>" \
  -var="kubernetes_version=<a version from the list above>"
```

Cluster creation takes several minutes. This is normal OKE behavior,
not a stuck `apply`.

## Where to start

- `terraform output cluster_id` gives you the cluster's OCID.
  `oci ce cluster get --cluster-id <id>` shows its `endpoints`,
  including a `public-endpoint`.
- Try reaching that endpoint with `curl`, from outside the VCN, with no
  kubeconfig and no credential at all.
- Look at what you get back. It doesn't need to be a 200 to tell you
  something real about what's running there.
- Check `main.tf` for what actually controls whether that endpoint has
  a public IP, and compare it to what controls the worker nodes'
  networking.

## Cleanup

```bash
terraform destroy
```

This also takes several minutes for the cluster itself. Verify
independently that it's really gone (`oci ce cluster get` should show
`DELETED`), not just that the command exited cleanly. See
`manifest.yml` for the resources this scenario creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
