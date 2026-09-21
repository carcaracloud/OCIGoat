# SCN-NET-002: Solution

## Root cause

Two Network Security Group rules exist on `target`'s two NSGs:

- `protected` allows ingress on port 8080, with `source` set to the
  `trusted` NSG.
- `incidental` allows ingress on port 3000, with `source` also set to
  the `trusted` NSG.

Oracle documents this source type directly:

> "for an NSG security rule's source (for ingress rules)... you can
> specify an NSG instead of a CIDR. This means you can easily write
> security rules to control traffic between two NSGs in the same VCN."

Source: [Network Security Groups](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm), Oracle documentation.

Read that rule the way an operator managing `incidental` would: "add
whatever needs to reach my port 3000 service to `trusted`." Nothing in
that sentence, or in `incidental`'s own configuration, mentions
`protected`. But an NSG rule with `source = trusted` doesn't check
*why* a VNIC is in `trusted`, only *whether* it is. `prober` was added
to `trusted` to reach `incidental`'s port 3000. That single membership
also satisfies `protected`'s rule, because both rules trust the exact
same group, independently, for reasons that have nothing to do with
each other.

A VNIC can belong to up to five NSGs at once, confirmed in the same
source, and the Console shows each NSG's own rules but never a single
view of every other NSG that also trusts it.

## How to confirm it, step by step

From `prober`, reach the service the membership was ostensibly for:

```bash
curl -m 5 -o /dev/null -w 'HTTP %{http_code}\n' http://<target-private-ip>:3000/
```

`HTTP 200`. Now reach the one nobody meant to grant:

```bash
curl -m 5 -o /dev/null -w 'HTTP %{http_code}\n' http://<target-private-ip>:8080/
```

Also `HTTP 200`, from an instance that is a member of exactly one NSG
(`trusted`), never `protected`, and never anything that references
`protected` directly.

## What this does and doesn't prove

It proves that trusting an NSG as a rule's `source` means trusting
every current and future member of it, for any reason that group
exists, not just the reason that motivated the rule being written. It
does not prove a flaw in Oracle's platform: NSG-to-NSG rules and the
five-NSG membership limit are both documented, and both behaved exactly
as documented here. It doesn't demonstrate any detection or alerting
for this pattern, native or otherwise, because that wasn't researched
for this scenario. The two HTTP services in this lab are fixtures, not
stand-ins for any specific real workload.

## Remediation

- Treat every NSG used as a `source` in a rule as a trust boundary
  shared by everyone who is, or will be, a member of it, not by the
  specific workload that originally justified the membership.
- Before adding a VNIC to an existing NSG for a narrow purpose, check
  every other NSG in the VCN that references it as a source, not just
  the one rule you're trying to satisfy.
- Prefer creating a new, narrowly scoped NSG over reusing an existing
  one, when the two use cases don't actually need to share trust.
- Periodically audit which NSGs are used as another NSG's `source`, and
  cross-reference against actual VNIC membership. There's no single
  Console view that does this for you.
