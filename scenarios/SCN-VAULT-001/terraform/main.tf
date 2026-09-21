terraform {
  required_version = ">= 1.5.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "9.2.0"
    }
  }
}

provider "oci" {
  auth = "APIKey"
}

variable "compartment_id" {
  type = string
}

variable "tenancy_ocid" {
  type = string
}

variable "test_user_email" {
  type = string
}

variable "test_user_api_public_key" {
  type = string
}

resource "oci_kms_vault" "this" {
  compartment_id = var.compartment_id
  display_name   = "ocigoat-scn-vault-001-vault"
  vault_type     = "DEFAULT"
}

resource "oci_kms_key" "this" {
  compartment_id      = var.compartment_id
  display_name        = "ocigoat-scn-vault-001-key"
  management_endpoint = oci_kms_vault.this.management_endpoint

  key_shape {
    algorithm = "AES"
    length    = 32
  }

  protection_mode = "SOFTWARE"
}

resource "oci_vault_secret" "intended" {
  compartment_id = var.compartment_id
  vault_id       = oci_kms_vault.this.id
  key_id         = oci_kms_key.this.id
  secret_name    = "ocigoat-scn-vault-001-intended"

  secret_content {
    content_type = "BASE64"
    content      = base64encode("SCN-VAULT-001 fixture. intended secret, safe to read.")
  }
}

resource "oci_vault_secret" "not_intended" {
  compartment_id = var.compartment_id
  vault_id       = oci_kms_vault.this.id
  key_id         = oci_kms_key.this.id
  secret_name    = "ocigoat-scn-vault-001-not-intended"

  secret_content {
    content_type = "BASE64"
    content      = base64encode("SCN-VAULT-001 fixture. not-intended secret, represents an out-of-scope credential.")
  }
}

resource "oci_identity_group" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-vault-001-operator"
  description    = "SCN-VAULT-001 test group"
}

resource "oci_identity_user" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-vault-001-operator"
  description    = "SCN-VAULT-001 test user"
  email          = var.test_user_email
}

resource "oci_identity_user_group_membership" "test_operator" {
  group_id = oci_identity_group.test_operator.id
  user_id  = oci_identity_user.test_operator.id
}

resource "oci_identity_api_key" "test_operator" {
  user_id   = oci_identity_user.test_operator.id
  key_value = var.test_user_api_public_key
}

resource "oci_identity_policy" "test_operator_grant" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-vault-001-operator-policy"
  description    = "SCN-VAULT-001 vulnerable policy"

  statements = [
    "Allow group id ${oci_identity_group.test_operator.id} to read secret-family in compartment id ${var.compartment_id}"
  ]
}

output "vault_id" {
  value = oci_kms_vault.this.id
}

output "intended_secret_id" {
  value = oci_vault_secret.intended.id
}

output "not_intended_secret_id" {
  value = oci_vault_secret.not_intended.id
}

output "test_user_ocid" {
  value = oci_identity_user.test_operator.id
}

output "test_user_api_key_fingerprint" {
  value = oci_identity_api_key.test_operator.fingerprint
}

output "tenancy_ocid" {
  value = var.tenancy_ocid
}
