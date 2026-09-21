# SCN-STORAGE-002: Solution

## Root cause

The bucket has neither `versioning` nor `retention_rules` set. Oracle
documents exactly what the first of those does:

> "By default, a bucket is created with versioning Disabled... Objects
> in a version enabled bucket are protected from overwrites and
> deletions. Previous versions of the same object will be available in
> the bucket."

Source: [`objectstorage_bucket.html.markdown`](https://github.com/oracle/terraform-provider-oci/blob/master/website/docs/r/objectstorage_bucket.html.markdown), Terraform provider `oracle/oci`.

Read that closely and the default is the interesting part: a bucket
that has never had versioning touched is exactly as unprotected as one
that has it explicitly disabled. Nothing about this bucket being named
for backups, used for backups, or treated as a backup destination by
convention changes any of that. `manage objects` is exactly what a
legitimate backup job would need to write into it, and it's exactly
what silently and permanently destroys the previous contents the
moment anything overwrites an object here.

## How to confirm it, step by step

Read the object first, to establish a baseline:

```bash
oci os object get --namespace <namespace> --bucket-name <bucket> --name <object> --file -
```

Overwrite it with the test user's credential:

```bash
echo "overwritten" > new-content.txt
oci os object put --namespace <namespace> --bucket-name <bucket> --name <object> --file new-content.txt --force --profile <test-user-profile>
```

Try to find a previous version:

```bash
oci os object list-object-versions --namespace <namespace> --bucket-name <bucket> --prefix <object>
```

This returns exactly one version: the one you just wrote. The original
is not listed, not recoverable, and not anywhere.

## What this does and doesn't prove

It proves that a bucket's name or intended purpose carries no technical
weight on its own. `versioning` and `retention_rules` are the actual
controls, both opt-in, and their absence produces no warning anywhere
in the bucket's configuration. It doesn't prove a flaw in Oracle's
platform: both controls exist, are documented, and one line of
Terraform each would have prevented this. It doesn't demonstrate
anything about how any real organization treats its backups, the
scenario's assumption that "this bucket is for backups" is the thing
being tested, not a claim about anyone's actual infrastructure.

## Remediation

- Enable `versioning = "Enabled"` on any bucket meant to hold anything
  that needs to survive an accidental or malicious overwrite.
- Add `retention_rules` for backup or compliance data that needs a
  guaranteed minimum retention window regardless of who has write
  access.
- Never treat a bucket's name, prefix convention, or stated purpose as
  a substitute for the technical control that actually provides
  durability.
- Audit `versioning` across every bucket in a tenancy whose name
  suggests backup, archive, or audit-log use. A default value is not
  the same as a deliberate one.
