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

variable "test_user_api_public_key" {
  type = string
}

resource "oci_identity_group" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-002-operator"
  description    = "SCN-IAM-002 test group"
}

resource "oci_identity_user" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-002-operator"
  description    = "SCN-IAM-002 test user"
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

resource "oci_identity_group" "privileged_target" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-002-privileged-target"
  description    = "SCN-IAM-002 fixture privileged group"
}

resource "oci_identity_policy" "test_operator_grant" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-002-operator-policy"
  description    = "SCN-IAM-002 vulnerable policy"

  statements = [
    "Allow group id ${oci_identity_group.test_operator.id} to use groups in tenancy",
    "Allow group id ${oci_identity_group.test_operator.id} to use users in tenancy"
  ]
}

resource "oci_identity_policy" "privileged_target_grant" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-002-target-policy"
  description    = "SCN-IAM-002 canary policy"

  statements = [
    "Allow group id ${oci_identity_group.privileged_target.id} to inspect dynamic-groups in tenancy"
  ]
}

output "test_user_ocid" {
  value = oci_identity_user.test_operator.id
}

output "test_user_api_key_fingerprint" {
  value = oci_identity_api_key.test_operator.fingerprint
}

output "privileged_target_group_ocid" {
  value = oci_identity_group.privileged_target.id
}

output "tenancy_ocid" {
  value = var.tenancy_ocid
}
