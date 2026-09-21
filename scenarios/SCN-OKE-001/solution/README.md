# SCN-OKE-001: Solution

## Root cause

The cluster's `endpoint_config.is_public_ip_enabled` is set to `true`.
This is a separate setting from anything controlling the worker nodes'
networking. Oracle documents it plainly:

> "is_public_ip_enabled - (Optional) Whether the cluster should be
> assigned a public IP address. Defaults to false. If set to true on a
> private subnet, the cluster provisioning will fail."

Source: [`containerengine_cluster.html.markdown`](https://github.com/oracle/terraform-provider-oci/blob/master/website/docs/r/containerengine_cluster.html.markdown), Terraform provider `oracle/oci`.

The Kubernetes API endpoint and the worker nodes are two distinct
network surfaces in OKE. Keeping node pools on a private subnet says
nothing about the control plane. A cluster can have every worker node
fully isolated from the internet and still have its API server
reachable from anywhere, if this one setting was left on.

## How to confirm it, step by step

Get the cluster's endpoints:

```bash
oci ce cluster get --cluster-id <cluster-ocid> --query 'data.endpoints'
```

`public-endpoint` is a real, internet-routable address on port 6443.

Hit it, with nothing but `curl`:

```bash
curl -sk https://<public-endpoint>/version
```

The response is a genuine `kube-apiserver` error envelope, reachable
from outside the VCN with no kubeconfig, no VPN, and no bastion:

```json
{
  "kind": "Status",
  "apiVersion": "v1",
  "status": "Failure",
  "message": "Unauthorized",
  "reason": "Unauthorized",
  "code": 401
}
```

## What this does and doesn't prove

It proves that a Kubernetes API endpoint's public/private setting is
independent of the worker nodes' own networking, and that a cluster
believed to be internal can still be identifiable and reachable from the
internet without any credential. It does not prove the cluster is
compromised. The response above is a `401`, not a `200`: the API server
is still requiring authentication for anything beyond confirming its own
existence. Reachability told you a real Kubernetes control plane is
sitting at that address. It told you nothing about RBAC, nothing about
any leaked credential, and nothing about whether an actual breach is
possible from here. That's a different, unresearched question.

It also doesn't prove a flaw in Oracle's platform. The default is
private, and the provider documents exactly what flipping the setting
does. The mistake is an operator assuming that a private subnet for
workers implies a private cluster, when OKE never made that guarantee.

## Remediation

- Set `endpoint_config.is_public_ip_enabled = false` unless there's a
  specific, deliberate reason to reach the API server from the public
  internet.
- If public access is genuinely needed, restrict it with
  `endpoint_config.nsg_ids` scoped to known source ranges, instead of
  leaving the security list open to `0.0.0.0/0`.
- Prefer accessing a private cluster's API server through a bastion
  host or VPN, the same pattern already used for private compute
  instances.
- Don't treat "workers are private" and "cluster is private" as the
  same statement when auditing OKE clusters. Check the endpoint's own
  configuration explicitly, every time.
