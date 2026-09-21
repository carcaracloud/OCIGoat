# SCN-IAM-002: Solution

## Root cause

The test user's group has two statements: `use groups in tenancy` and
`use users in tenancy`. Each one, alone, looks limited. `use` sits below
`manage` in OCI's cumulative permission hierarchy, and the table for
each resource-type on its own doesn't grant much beyond updating that
resource-type.

The catch is `AddUserToGroup`. Oracle's own permission table lists it
under `groups: use`, with a note attached: it also needs `use users`.
The `users: use` entry mirrors this, needing `use groups` in return.
Neither statement grants `AddUserToGroup` by itself. Together, they do,
across the entire tenancy.

Source: [IAM Policy Reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/iampolicyreference.htm), Oracle Cloud Infrastructure documentation.

Cumulative verbs never cross resource-types. That rule holds here too.
What's easy to miss is that a single API operation can require two
separate resource-type grants to line up before it becomes available,
and nothing in either statement alone hints at that.

## How to confirm it, step by step

Check what the test user can reach before touching anything:

```bash
oci iam dynamic-group list --profile SCN-IAM-002
```

This fails with `NotAuthorizedOrNotFound`. No grant on that
resource-type at all.

Read the two policies to see the actual grants:

```bash
oci iam policy get --policy-id $(terraform output -raw ...) --profile DEFAULT
```

The test user's group: `use groups in tenancy`, `use users in tenancy`.
The second group: `inspect dynamic-groups in tenancy`, nothing else.

Now use exactly what the test user already has to join that second
group:

```bash
oci iam group add-user \
  --group-id $(terraform output -raw privileged_target_group_ocid) \
  --user-id $(terraform output -raw test_user_ocid) \
  --profile SCN-IAM-002
```

This succeeds. Wait a few seconds for the change to propagate, then
repeat the first check:

```bash
oci iam dynamic-group list --profile SCN-IAM-002
```

This now succeeds too. The test user inherited the second group's grant
just by joining it, using permissions that individually looked
insufficient for that. The listing includes a fixture dynamic group;
read it directly:

```bash
oci iam dynamic-group get --dynamic-group-id $(terraform output -raw flag_target_dynamic_group_ocid) --profile SCN-IAM-002
```

Its `description` holds an `OCIGOAT{...}` flag generated fresh for
this deployment. Submit it with `ocigoat submit SCN-IAM-002 <flag>`.

## What this does and doesn't prove

It proves that `use groups` and `use users`, granted together, let a
principal add itself to any group visible in that scope, including one
that carries more privilege than the principal ever had directly. It
does not prove a flaw in Oracle's platform. The cross-resource-type
requirement is documented explicitly in the permission table; the
mistake is an operator granting both verbs to the same group without
realizing what the pair adds up to.

It doesn't demonstrate access to the tenancy's real `Administrators`
group. The privileged group in this lab is a fixture, created and
destroyed by this scenario, to keep the blast radius contained. The
lesson generalizes to any group in scope, administrative or not, but
that isn't tested directly here.

## Remediation

- Never grant `use groups` and `use users` to the same principal unless
  that principal is meant to manage group membership tenancy-wide.
  Individually they look safe; together they aren't.
- Audit for this pair specifically. A policy review that checks each
  statement in isolation will miss this every time.
- Prefer scoping group and user management to a dedicated
  administrative identity, not a general-purpose operational one.
- Treat any principal with both verbs as equivalent to someone who can
  join any group in scope, and apply the same scrutiny you'd apply to
  direct group membership grants.
