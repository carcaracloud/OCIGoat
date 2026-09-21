# SCN-VAULT-001: Solution

## Root cause

The test user's group has exactly one policy statement:

```
Allow group id <test-operator-group> to read secret-family in compartment id <compartment>
```

That statement is scoped by compartment only. Oracle's own policy
reference documents two condition variables that exist specifically to
narrow a Vault/Secrets grant further, to one named secret:

> `target.secret.name`, `target.secret.id`

Source: [Details for Vault, Key Management, and Secret Management](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/keypolicyreference.htm),
Oracle IAM Policy Reference.

Neither condition variable appears in the statement above. Without
them, `read secret-family in compartment C` means exactly what it says:
read access to every secret in that compartment, not to whichever one
secret the operator had in mind when they wrote the policy.

## How to confirm it, step by step

Set up a CLI profile using the test user's OCID, its API key
fingerprint, and the private key you generated. Then read both secret
OCIDs from the Terraform output with that profile:

```bash
oci secrets secret-bundle get --secret-id <intended-secret-ocid> --profile <your-profile>
oci secrets secret-bundle get --secret-id <not-intended-secret-ocid> --profile <your-profile>
```

Both calls succeed. The second one is the one that matters: the test
user was never meant to see that secret, and nothing in the policy
statement actually stops them.

## What this does and doesn't prove

It proves that Vault/Secrets policies default to the same granularity
as the resource-type they're written against, and that resource-type
in this case is the whole `secret-family`, not an individual secret.
Fine-grained scoping exists and is one condition variable away, but is
opt-in and silent about its own absence: nothing about writing the
statement without `target.secret.name` produces a warning, an error, or
even a difference in how the policy reads at a glance.

It doesn't prove a flaw in Oracle's platform. The condition variables
are documented, and a policy written with them would have blocked
exactly this. It doesn't prove anything about detection: whether
reading a secret outside a policy's intended scope triggers any kind of
alert wasn't researched for this scenario, and this lab makes no claim
about it either way.

## Remediation

- Always pair `secret-family` (or any Vault/Secrets grant broader than
  a single action) with `target.secret.name` or `target.secret.id` when
  the intent is to grant access to one specific secret, not the whole
  compartment.
- Store secrets that different audiences should access in different
  compartments, so a compartment-scoped policy is never a proxy for
  "everything in here is fine for this group to read."
- Review every Vault/Secrets policy statement in a tenancy for the
  presence of a target condition before treating "scoped to a
  compartment" as equivalent to "scoped to a secret."
- Prefer least privilege at the individual secret level for anything
  that isn't genuinely meant to be shared compartment-wide, the same
  discipline already expected for `manage`/`use` verbs elsewhere in
  IAM.
