# SCN-BASTION-001: Solution

## Root cause

The Bastion is created with:

```
client_cidr_block_allow_list = ["0.0.0.0/0"]
```

Oracle documents this argument as the client-origin control for the
service:

> "A list of address ranges in CIDR notation that you want to allow to
> connect to sessions hosted by this bastion."

Source: [`bastion_bastion.html.markdown`](https://github.com/oracle/terraform-provider-oci/blob/master/website/docs/r/bastion_bastion.html.markdown), Terraform provider `oracle/oci`.

A Bastion sitting in front of a private instance looks, by itself, like
a security boundary: the target has no public IP, so surely only
"the right people" can reach it. But the Bastion's own network
allowlist is a separate, opt-in setting. Left at `0.0.0.0/0`, it places
no restriction at all on where a session request comes from. The test
user's IAM permission to create a session (`manage bastion-session`,
`use bastion`, plus read access to find the target) is the only other
gate, and this lab grants that permission deliberately, as a fixture,
specifically to isolate the network-origin control as the one thing
actually being tested.

## How to confirm it, step by step

From a machine with no special relationship to the tenancy, create a
port forwarding session:

```bash
oci bastion session create-port-forwarding \
  --bastion-id <bastion-ocid> \
  --target-resource-id <target-ocid> \
  --target-port 22 \
  --target-private-ip <target-private-ip> \
  --ssh-public-key-file session-key.pub \
  --profile <test-user-profile>
```

The response includes a ready-to-use `ssh-metadata.command`. Open the
tunnel with it, then SSH through to the target using the key already
authorized there:

```bash
ssh -i session-key -N -L 2222:<target-private-ip>:22 -p 22 \
  <session-ocid>@host.bastion.<region>.oci.oraclecloud.com &
ssh -i target-key -p 2222 opc@localhost
```

This reaches an instance with no public IP at all, from a network the
organization never approved, vetted, or even knew about.

```bash
cat flag.txt
```

Its content is an `OCIGOAT{...}` flag generated fresh for this
deployment. Submit it with `ocigoat submit SCN-BASTION-001 <flag>`.

## What this does and doesn't prove

It proves that a Bastion's own presence in an architecture diagram
doesn't restrict who can use it; `client_cidr_block_allow_list` is the
setting that does that job, and it's optional. It doesn't prove the
IAM side was also broken: the permission to create a session is a
fixture this lab hands to the player on purpose, to keep the network
control as the only variable under test. It doesn't prove the Bastion
service is inherently insecure. The control exists, is documented, and
a narrower CIDR list would have stopped this specific exploitation. It
doesn't demonstrate any additional layer, like session recording or
MFA, that a real organization might have on top.

## Remediation

- Set `client_cidr_block_allow_list` to the narrowest range that
  covers where session requests should legitimately originate (a
  corporate VPN egress range, for example), at creation time, not as
  a follow-up.
- Don't treat "the target has no public IP" as equivalent to "the
  target is only reachable by trusted people." The Bastion is
  infrastructure for restricting access; it doesn't restrict anything
  by existing.
- Pair the network control with the minimum IAM permissions needed to
  create and use sessions. Neither control alone is sufficient; both
  are required to actually narrow who can connect.
- Audit `client_cidr_block_allow_list` across every Bastion in a
  tenancy the same way you'd audit a security list or NSG rule open to
  `0.0.0.0/0`.
