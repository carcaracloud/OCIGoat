# SCN-REGISTRY-001: Solution

## Root cause

The repository's `is_public` attribute is set to `true`. Repositories
in Container Registry are private by default, and Oracle documents
exactly what flipping this does:

> "Can repos be public? Yes, an administrator of the tenancy can make
> any repo public. This means that if a user has the complete path to
> the image, they can pull it, with no authentication needed."

Source: [Container Registry FAQ](https://www.oracle.com/cloud/cloud-native/container-registry/faq/), Oracle Cloud Infrastructure.

Unlike a Pre-Authenticated Request, Oracle never claims this path is
unguessable. A public repository's protection is entirely down to
whatever naming convention the operator chose, not anything the
platform enforces.

## How to confirm it, step by step

If you don't have Docker available, the Registry HTTP API V2 works
directly with `curl`. Request a token with no credentials at all:

```bash
curl "https://<region>.ocir.io/20180419/docker/token?service=<region>.ocir.io&scope=repository:<namespace>/ocigoat-scn-registry-001-repo:pull"
```

The response is a real JWT, and decoding its payload shows exactly who
the registry thinks is asking:

```json
{"userId":"anon-...","tenantId":"anon-...","claims":[]}
```

An identity prefixed `anon-`, granted `pull` on this specific
repository, with nothing supplied to prove who's asking. That's the
proof the repository is genuinely public, not just reachable.

Use that token to pull the manifest:

```bash
curl -H "Authorization: Bearer <token>" \
  https://<region>.ocir.io/v2/<namespace>/ocigoat-scn-registry-001-repo/manifests/latest
```

This returns the image manifest in full. Follow the layer digest it
contains to `/v2/<namespace>/.../blobs/<digest>` with the same token,
and the layer content downloads, unauthenticated, end to end.

## What this does and doesn't prove

It proves that a public Container Registry repository issues real,
scoped anonymous credentials on demand, and that anyone with the
repository's path can retrieve every layer of every image in it. It
doesn't prove a flaw in Oracle's platform. Repositories are private by
default, and the FAQ states the public behavior plainly; the mistake is
an operator making a repository public without weighing that its path,
not any cryptographic secret, is now the only thing standing between the
image and the public internet.

It doesn't demonstrate anything about the image's real contents. The
fixture pushed here is a single harmless text file, not a stand-in for
what a real CI/CD pipeline would push.

## Remediation

- Keep repositories private by default. Reserve `is_public` for images
  genuinely meant for open distribution, the same bar you'd apply to a
  public GitHub release artifact.
- If you need to share one image without exposing an entire
  repository's history, prefer generating scoped, revocable credentials
  for a service account over flipping a whole repository public.
- Audit `is_public` across every repository in a tenancy. Nothing in
  the Console highlights this the way it highlights, say, a security
  list rule.
- Never rely on an obscure repository name as the actual control. Name
  predictability is an operational convenience, not a security
  boundary; if it needs enforcement, apply an IAM policy scoped to the
  repository, not a hard-to-guess path.
