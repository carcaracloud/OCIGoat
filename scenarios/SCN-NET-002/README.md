# SCN-NET-002: Transitive Reachability Through a Shared Network Security Group

**Category:** network | **Difficulty:** medium

## Objective

Two Network Security Groups protect two unrelated services on the same
instance. Neither rule mentions the other NSG. You've been handed SSH
access to a third instance that was added to a shared NSG for one of
those two services. Find out whether that also reaches the one it
wasn't added for.

## Prerequisites

- Terraform >= 1.5.0
- A compartment OCID you're authorized to deploy into
- An SSH keypair for accessing the `prober` instance

## Deploy

```bash
cd terraform
terraform init
terraform apply \
  -var="compartment_id=<your-compartment-ocid>" \
  -var="operator_ssh_public_key=$(cat ~/.ssh/id_ed25519.pub)"
```

## Where to start

- `terraform output` gives you `prober_public_ip` and
  `target_private_ip`. SSH into `prober` with the key you provided.
- Check `main.tf` for which NSG each instance belongs to, and which
  NSG each security rule uses as its `source`. `prober` is only a
  member of one NSG.
- From inside `prober`, try reaching `target` on both port 3000 and
  port 8080 with `curl`. Nothing in `prober`'s own NSG membership was
  written with port 8080 in mind.
- Ask yourself what `prober` would need to belong to, on paper, to
  justify reaching port 8080, then check whether it actually belongs
  to that.

## Cleanup

```bash
terraform destroy
```

Verify independently that both instances and all three NSGs are
really gone. See `manifest.yml` for the resources this scenario
creates.

## Solution

Don't open `solution/` until you've formed your own theory. It has the
full explanation, root cause, and remediation.
