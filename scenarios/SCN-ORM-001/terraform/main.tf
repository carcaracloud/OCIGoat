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

resource "oci_identity_group" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-orm-001-operator"
  description    = "SCN-ORM-001 test group"
}

resource "oci_identity_user" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-orm-001-operator"
  description    = "SCN-ORM-001 test user"
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
  name           = "ocigoat-scn-orm-001-operator-policy"
  description    = "SCN-ORM-001 vulnerable-by-verb policy"

  statements = [
    "Allow group id ${oci_identity_group.test_operator.id} to read orm-stacks in compartment id ${var.compartment_id}"
  ]
}

output "test_user_ocid" {
  value = oci_identity_user.test_operator.id
}

output "test_user_api_key_fingerprint" {
  value = oci_identity_api_key.test_operator.fingerprint
}
