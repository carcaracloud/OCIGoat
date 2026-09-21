# SCN-DATABASE-001: Solution

## Root cause

The Autonomous Database was created without `is_access_control_enabled`
set, and without any `whitelisted_ips`. Oracle documents exactly what
that means:

> "Specifying an access control list blocks all IP addresses that are
> not in the ACL list from accessing the database."

Source: [Access Control Rules](https://docs.oracle.com/en-us/iaas/Content/Database/autonomous-database-shared/doc/access-control-rules-autonomous.html),
Oracle documentation.

Read that sentence carefully and it only describes what happens
**after** an ACL is specified. It says nothing about the state before
that. The state before that, confirmed directly against a real
database in this scenario's own validation, is `null`, not `false` and
not an empty list: the field simply was never set, which is a distinct
state from "configured and denying everyone." Without an ACL, the
default is permissive: any IP can attempt a connection, to both the
SQL listener and the same list of HTTPS tools this scenario used to
prove it, among them Database Actions, Oracle APEX, and Oracle REST
Data Services.

Source: [Terraform provider `oracle/oci`](https://github.com/oracle/terraform-provider-oci/blob/master/website/docs/r/database_autonomous_database.html.markdown), arguments `is_access_control_enabled` and `whitelisted_ips`.

## How to confirm it, step by step

Get the database's Database Actions URL:

```bash
oci db autonomous-database get \
  --autonomous-database-id <adb-ocid> \
  --query 'data."connection-urls"."ords_url"' --raw-output
```

Hit it with nothing but `curl`, no headers, no wallet:

```bash
curl -sk -L <ords-url>
```

This returns a real ORDS landing page, HTTP 200, from a machine that
was never granted access to anything on this database, reachable from
outside the tenancy with no VPN and no bastion.

## What this does and doesn't prove

It proves that "no ACL configured" and "ACL configured but empty" are
opposite states, and that the first one is the one Oracle ships by
default. An operator who reads "Secure access from everywhere" in the
Console and assumes that phrase describes a deliberate security
posture is wrong: it describes the absence of one. It does not prove
the database was compromised. The response is a login page, not a
successful authentication: `admin_password` in this scenario's
Terraform is never handed to the player, and reaching the HTTPS front
door proves nothing about SQL-level access, which remains a second,
untested layer.

It also doesn't prove a flaw in Oracle's platform. The
`is_access_control_enabled` argument exists precisely to close this
off, is documented, and takes one line of Terraform to set. The mistake
is an operator who meant to configure it "later" not realizing the
database is already fully reachable during that entire window.

## Remediation

- Set `is_access_control_enabled = true` with an explicit
  `whitelisted_ips` list at creation time, not as a follow-up step.
  There is no safe intermediate state between "created" and "ACL
  configured."
- Treat a database with no ACL the same as a database with a public IP
  and no firewall, because that's what it is, for both the SQL
  listener and every HTTPS tool Oracle lists as subject to the same
  control.
- Audit `is-access-control-enabled` across every Autonomous Database in
  a tenancy. A `null`/absent value is not a safer default than an
  explicit `false` would be; it's the same exposure with a less
  visible signal.
- Prefer a Private Endpoint over a public one plus an ACL when the
  database never needs to be reachable from outside its VCN at all.
