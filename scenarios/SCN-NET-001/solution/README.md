# SCN-NET-001: Solution

## Root cause

The subnet's Security List has no ingress rules at all. By itself, that
should block every inbound connection. But the instance's VNIC is also a
member of a Network Security Group (NSG) that has an ingress rule allowing
`0.0.0.0/0` on the service's port.

Security Lists and NSGs are not layered the way you might expect from
other clouds where "most restrictive wins." On OCI, when a VNIC is subject
to both a Security List and one or more NSGs, the effective rule set is
the **union** of all of them. Traffic is allowed if *any* applicable rule
allows it, not only if all of them agree.

Oracle documents this directly:

> "If you use both security lists and network security groups, the set of
> rules that applies to a particular VNIC is the union of these items: the
> security rules in the security lists associated with the VNIC's subnet;
> the security rules in all NSGs that the VNIC is in."

Source: [Security Rules](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm), Oracle Cloud Infrastructure documentation.

A Security List that looks locked down tells you nothing about what an
NSG attached to the same VNIC might be allowing.

## How to confirm it, step by step

Check the Security List first. This alone would suggest the instance
isn't reachable:

```bash
oci network security-list get --security-list-id $(terraform output -raw security_list_id)
```

`ingress-security-rules` comes back empty. Looks locked down. It isn't.

Now check the NSG:

```bash
oci network nsg rules list --nsg-id $(terraform output -raw network_security_group_id)
```

One rule: `INGRESS`, protocol `6` (TCP), source `0.0.0.0/0`, the service
port. That's the actual reason it's reachable.

Confirm from outside the VCN, not from inside it. That wouldn't test
anything real:

```bash
curl $(terraform output -raw test_service_url)
```

## What this does and doesn't prove

It proves that a permissive NSG rule is sufficient by itself to make a
port reachable, regardless of what the Security List says. It does not
prove that reachability equals compromise. Nothing here demonstrates
authentication bypass, code execution, or data access. The fixture
service is a static "hello world," deliberately, so the lesson stays
about the network layer and doesn't get muddled with an unrelated
application bug.

It also isn't an OCI vulnerability. Oracle's shared responsibility model
puts configuring network access (Security Lists, NSGs, gateways) on the
customer, not on Oracle. This scenario demonstrates a configuration
mistake a real operator can make, not a flaw in the platform.

## Remediation

- Don't treat a restrictive Security List as sufficient on its own. Check
  every NSG a VNIC belongs to.
- Prefer NSGs over Security Lists for anything workload-specific. They're
  scoped to the VNICs you actually attach them to instead of an entire
  subnet, which makes audits easier.
- Scope `source` to the smallest CIDR that actually needs access, not
  `0.0.0.0/0`, unless the service is genuinely meant to be public.
- Periodically enumerate every NSG in a compartment and diff its rules
  against what you expect. Nothing in the Console makes it obvious which
  NSGs are attached to which instances at a glance.
- If a service is meant to be internal only, don't rely on network
  controls alone. Put a load balancer or reverse proxy in front of it, or
  don't assign it a public IP in the first place.
