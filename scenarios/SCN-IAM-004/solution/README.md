# SCN-IAM-004: Solution

## Root cause

The dynamic group's matching rule is `instance.compartment.id =
'<compartment>'`. Oracle documents this rule type directly, as one of
the standard ways to define dynamic group membership:

> "instance.compartment.id = '<compartment_ocid>'"

Source: [Managing Dynamic Groups](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm), Oracle Cloud Infrastructure documentation.

A rule like this doesn't check who created an instance, why, or with
what permission level. It checks exactly one thing: is the instance's
compartment the one named in the rule. The test user's policy grants
`manage instance-family` in that same compartment, so it can launch an
instance there. The moment that instance exists, it satisfies the
matching rule on its own, and inherits whatever the dynamic group's
policy grants, independent of anything the test user itself was ever
authorized to do directly.

## How to confirm it, step by step

Before launching anything, check what the test user can reach directly:

```bash
oci os bucket list --compartment-id <compartment> --profile SCN-IAM-004
```

This fails. No grant on Object Storage at all.

Launch an instance in the same compartment, using only the permissions
the test user already has:

```bash
oci compute instance launch \
  --compartment-id <compartment> \
  --availability-domain <ad> \
  --shape VM.Standard.E2.1.Micro \
  --image-id <oracle-linux-8-image> \
  --subnet-id <subnet-from-output> \
  --assign-public-ip true \
  --metadata '{"ssh_authorized_keys":"<your-ssh-public-key>"}' \
  --profile SCN-IAM-004 \
  --wait-for-state RUNNING
```

Connect once it's running, then run the same check as before, but from
inside the instance, authenticated as the instance itself:

```bash
oci os bucket list --compartment-id <compartment> --auth instance_principal
```

This succeeds. The instance you just created, with no credential of its
own beyond what OCI issues it automatically, can do something the test
user that created it never could.

## What this does and doesn't prove

It proves that a dynamic group scoped by compartment membership doesn't
distinguish "the workload I meant to grant this access to" from "any
instance anyone with launch permission in this compartment decides to
create." The matching rule is documented to work exactly this way; the
mistake is an operator assuming a compartment boundary implies intent,
when it's really just a location.

It doesn't prove a flaw in Oracle's platform, and it doesn't prove that
an attacker could discover this matching rule on their own. This lab
hands you the rule's exact text as your starting point, the same way it
hands you the test user's credential. A real attacker without that
information would need some other way to learn it; that's a separate,
unresearched question.

## Remediation

- Scope dynamic group matching rules to something an attacker with
  ordinary launch permission can't recreate: a specific instance OCID,
  a defined tag applied only by a trusted automation identity, or a
  compartment dedicated exclusively to instances that are meant to hold
  that privilege, with launch permission itself tightly restricted.
- Never grant `manage instance-family` in a compartment that also hosts
  a dynamic group matching that same compartment, unless every principal
  with launch permission there is meant to inherit what the dynamic
  group grants.
- Audit dynamic group matching rules the same way you'd audit an IAM
  policy statement. A rule that reads as a location filter is, in
  effect, a privilege grant to anyone who can place a resource there.
