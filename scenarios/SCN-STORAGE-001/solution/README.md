# SCN-STORAGE-001: Solution

## Root cause

The bucket's `access_type` is set to `ObjectRead`. Object Storage
buckets are private by default; `ObjectRead` is one of two ways to make
one public, and it grants more than most people expect from the name.

Oracle documents both public options directly, in the same sentence
pair:

> "When ObjectRead is enabled on the bucket, public access is allowed
> for the GetObject, HeadObject, and ListObjects operations. When
> ObjectReadWithoutList is enabled on the bucket, public access is
> allowed for the GetObject and HeadObject operations."

Source: [`objectstorage_bucket.html.markdown`](https://github.com/oracle/terraform-provider-oci/blob/master/website/docs/r/objectstorage_bucket.html.markdown), Terraform provider `oracle/oci`.

Read that closely and the naming is backwards from what it sounds like.
`ObjectRead`, the simpler and more obvious-sounding name, is the option
that includes `ListObjects`, full directory browsing of the bucket.
`ObjectReadWithoutList`, the option with the longer, more restrictive
sounding name, is the one that actually withholds something:
listing. If an operator's intent was "let people download a file if
they have the link, nothing more," `ObjectReadWithoutList` is what they
wanted. `ObjectRead` gives away the bucket's entire contents to anyone
who asks, whether or not they had a link to begin with.

## How to confirm it, step by step

Request the bucket's listing endpoint directly, with no credentials:

```bash
curl https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/ocigoat-scn-storage-001-bucket/o/
```

This returns `{"objects":[{"name":"notes/handoff.txt"}]}`. No
authentication, no prior knowledge of the filename, nothing but the
bucket's own public URL.

Now request that object directly:

```bash
curl https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/ocigoat-scn-storage-001-bucket/o/notes/handoff.txt
```

This returns the file's contents in full, including an `OCIGOAT{...}`
flag generated fresh for this deployment. Submit it with `ocigoat
submit SCN-STORAGE-001 <flag>`.

## What this does and doesn't prove

It proves that `ObjectRead` exposes both the contents and the structure
of a bucket to anyone, unauthenticated, and that its name doesn't
signal this as clearly as `ObjectReadWithoutList`'s name signals its own
narrower scope. It doesn't prove a flaw in Oracle's platform. The
default is `NoPublicAccess`, and both public options are documented
plainly; the mistake is an operator picking the broader one without
reading past the first word of its name.

It doesn't demonstrate anything about the object's real content. The
file here is a fixture, written for this lab, not a stand-in for what
any real organization would actually store.

## Remediation

- Default to `ObjectReadWithoutList` for any bucket that needs public
  access at all. Only use `ObjectRead` when browsing the full bucket
  contents is an intended feature, not an oversight.
- Prefer Pre-Authenticated Requests over public buckets for sharing a
  specific object. A PAR scopes access to what was actually intended to
  be shared, with an expiry, instead of the whole bucket indefinitely.
- Audit `access_type` across every bucket in a tenancy periodically.
  Nothing in the Console distinguishes "public because someone meant to"
  from "public because someone picked the wrong option."
- Treat any object placed in a bucket with either public `access_type`
  as effectively public the moment it's uploaded, regardless of whether
  its name was meant to be secret.
