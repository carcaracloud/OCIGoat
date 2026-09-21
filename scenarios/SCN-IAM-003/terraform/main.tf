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

variable "tenancy_ocid" {
  type = string
}

variable "test_user_email" {
  type = string
}

variable "target_admin_email" {
  type = string
}

variable "test_user_api_public_key" {
  type = string
}

variable "flag_content" {
  type    = string
  default = "OCIGOAT{not-tracked}"
}

resource "oci_identity_group" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-003-operator"
  description    = "SCN-IAM-003 test group"
}

resource "oci_identity_user" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-003-operator"
  description    = "SCN-IAM-003 test user"
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
  name           = "ocigoat-scn-iam-003-operator-policy"
  description    = "SCN-IAM-003 vulnerable policy"

  statements = [
    "Allow group id ${oci_identity_group.test_operator.id} to manage users in tenancy"
  ]
}

resource "oci_identity_group" "target_admin_group" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-003-target-admin-group"
  description    = "SCN-IAM-003 fixture privileged group"
}

resource "oci_identity_user" "target_admin" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-003-target-admin"
  description    = "SCN-IAM-003 fixture impersonation target"
  email          = var.target_admin_email
}

resource "oci_identity_user_group_membership" "target_admin" {
  group_id = oci_identity_group.target_admin_group.id
  user_id  = oci_identity_user.target_admin.id
}

resource "oci_identity_policy" "target_admin_grant" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-003-target-policy"
  description    = "SCN-IAM-003 canary policy"

  statements = [
    "Allow group id ${oci_identity_group.target_admin_group.id} to inspect dynamic-groups in tenancy"
  ]
}

resource "oci_identity_dynamic_group" "flag_target" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-003-flag-target"
  description    = var.flag_content
  matching_rule  = "instance.compartment.id = '${var.tenancy_ocid}'"
}

output "test_user_ocid" {
  value = oci_identity_user.test_operator.id
}

output "test_user_api_key_fingerprint" {
  value = oci_identity_api_key.test_operator.fingerprint
}

output "target_admin_ocid" {
  value = oci_identity_user.target_admin.id
}

output "flag_target_dynamic_group_ocid" {
  value = oci_identity_dynamic_group.flag_target.id
}

output "tenancy_ocid" {
  value = var.tenancy_ocid
}
