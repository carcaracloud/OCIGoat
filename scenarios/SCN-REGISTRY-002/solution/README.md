# SCN-REGISTRY-002: Solution

## Root cause

The repository's `is_public` is `true`, the same setting from
`SCN-REGISTRY-001`:

> "`is_public` - (Optional) (Updatable) Whether the repository is
> public. A public repository allows unauthenticated access."

Source: [`artifacts_container_repository.html.markdown`](https://github.com/oracle/terraform-provider-oci/blob/master/website/docs/r/artifacts_container_repository.html.markdown), Terraform provider `oracle/oci`.

That setting alone was the whole story in `SCN-REGISTRY-001`. Here it's
only half of it. The fixture image was built from a Dockerfile that
writes a credential file in one layer and removes it with `RUN rm` in
a later one, a completely ordinary pattern for "I don't want this
lying around in the final image." But container image layers are not
edits, they're an append-only history. Each layer is an immutable diff
against the one before it. `RUN rm` doesn't erase anything from the
layer where the file was written; it adds a new layer on top with a
whiteout marker (a file named `.wh.<name>` in the OCI/Docker layer
spec) that tells the runtime "hide this file when you assemble the
final view." The original layer, whiteout marker and all, ships with
the image regardless.

## How to confirm it, step by step

Get an anonymous token and the manifest:

```bash
curl -s "https://<region-key>.ocir.io/20180419/docker/token?service=<region-key>.ocir.io&scope=repository:<namespace>/ocigoat-scn-registry-002-repo:pull" | python3 -c "import json,sys;print(json.load(sys.stdin)['token'])"
curl -s -H "Authorization: Bearer <token>" -H "Accept: application/vnd.docker.distribution.manifest.v2+json" "https://<region-key>.ocir.io/v2/<namespace>/ocigoat-scn-registry-002-repo/manifests/latest"
```

Pull the first layer (not the last one) and extract it:

```bash
curl -s -H "Authorization: Bearer <token>" "https://<region-key>.ocir.io/v2/<namespace>/ocigoat-scn-registry-002-repo/blobs/<first-layer-digest>" -o layer1.tar.gz
tar -xzOf layer1.tar.gz opt/app/config/credentials.txt
```

This prints the full, original content of the file that `RUN rm`
supposedly removed, anonymously, from a layer that shipped in the
public image the whole time.

## What this does and doesn't prove

It proves that "removed in a later build step" is not the same claim
as "absent from the published image." A public repository exposes
every layer's blob, and layers are cumulative history, not a diff
against the final state. It doesn't prove a flaw in Oracle's platform:
the registry is private by default, `is_public` is documented, and the
layer mechanics are a property of the container image format itself,
not something Oracle controls or could silently fix. It doesn't
demonstrate any scanning or detection: OCI Vulnerability Scanning
exists as a separate, opt-in service and wasn't used or evaluated
here. The credential in this lab is fake, standing in for the class of
mistake, not a real leak.

## Remediation

- Never write a secret into an image layer expecting a later `RUN rm`
  to remove it from the published artifact. It doesn't.
- Use multi-stage builds: write the secret only in a build stage that
  is never included in the final image's layer history.
- Use build-time secret mounts (e.g. `docker build --secret` /
  BuildKit's `RUN --mount=type=secret`) for anything that needs to be
  present only during the build, never persisted in any layer.
- Treat `is_public = true` as exposing the entire layer history, not
  just the running container's final filesystem, when deciding what's
  safe to leave in a public repository.
