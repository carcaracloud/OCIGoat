# Contributing to OCIGoat

## Reporting a bug or requesting a scenario

Open an issue. For a bug, include the scenario ID (or `ocigoat`
command) and exact error output. For a new scenario idea, describe the
OCI misconfiguration and what it lets a principal do that they
shouldn't be able to.

## The rule behind every scenario

Every technical claim about OCI behavior in this repo, an IAM verb, a
Terraform argument, a default value, has to be backed by Oracle's own
documentation or a real `terraform apply` against a live tenancy.
"This should work" or "this is probably how OCI handles it" is not
good enough; a PR that guesses at OCI behavior instead of citing or
testing it will be asked to do one or the other before merge.

## Adding a scenario

1. State the misconfiguration and the exact OCI mechanism it abuses,
   citing the relevant Oracle documentation page.
2. Write the Terraform (`scenarios/<SCN-ID>/terraform/main.tf`),
   pinning the `oracle/oci` provider version already used by the rest
   of the repo.
3. Apply it against a real tenancy and actually perform the
   exploitation you're describing, not just the deploy. Capture real
   command output for the `solution/README.md` walkthrough.
4. `terraform destroy`, then independently confirm every resource is
   gone (`oci ... get` returning `404` or a terminal state), not just
   a clean exit code.
5. Fill in `manifest.yml`, the player-facing `README.md` (objective,
   no spoilers), and `solution/README.md` (root cause, how to confirm
   it, what it does and doesn't prove, remediation), following the
   structure of an existing scenario in the same category.
6. Add the scenario to the table in the root `README.md`.

## Working on the `ocigoat` CLI

```bash
pip install -e ".[dev]"
pytest -q
```

Tests should not require real OCI credentials, `terraform`, or
`openssl` to be installed, mock those calls instead. If a change
touches `ocigoat create`/`destroy`, test it against at least one real
scenario end to end before opening the PR; the CLI manages real cloud
resources, and a bug in the destroy path can leave things running.

## Style

- Small, focused commits with a clear, lowercase, imperative-mood
  message (`add SCN-X scenario`, not `Added some stuff`).
- No filler text, no unexplained jargon, no claims you haven't
  verified.
- Match the existing structure of whatever you're editing rather than
  introducing a new pattern for the same thing.
