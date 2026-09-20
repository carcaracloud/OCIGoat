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

variable "compartment_id" {
  type = string
}

variable "test_user_email" {
  type = string
}

variable "test_user_api_public_key" {
  type = string
}

resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_id
  cidr_blocks    = ["10.1.0.0/16"]
  display_name   = "ocigoat-scn-iam-004-vcn"
  dns_label      = "ocigoatiam4"
}

resource "oci_core_internet_gateway" "this" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-iam-004-igw"
  enabled        = true
}

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-iam-004-rt-public"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.this.id
  }
}

resource "oci_core_security_list" "ssh" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-iam-004-sl-ssh"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"

    tcp_options {
      min = 22
      max = 22
    }
  }
}

resource "oci_core_subnet" "public" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.this.id
  cidr_block                 = "10.1.0.0/24"
  display_name               = "ocigoat-scn-iam-004-subnet-public"
  dns_label                  = "public"
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.ssh.id]
  prohibit_public_ip_on_vnic = false
  prohibit_internet_ingress  = false
}

resource "oci_identity_dynamic_group" "privileged" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-004-privileged-dg"
  description    = "SCN-IAM-004 dynamic group vulnerable to compartment self-enrollment"
  matching_rule  = "instance.compartment.id = '${var.compartment_id}'"
}

resource "oci_identity_policy" "privileged_dg_grant" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-004-dg-policy"
  description    = "SCN-IAM-004 canary policy"

  statements = [
    "Allow dynamic-group id ${oci_identity_dynamic_group.privileged.id} to read all-resources in compartment id ${var.compartment_id}"
  ]
}

resource "oci_identity_group" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-004-operator"
  description    = "SCN-IAM-004 test group"
}

resource "oci_identity_user" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-iam-004-operator"
  description    = "SCN-IAM-004 test user"
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
  name           = "ocigoat-scn-iam-004-operator-policy"
  description    = "SCN-IAM-004 vulnerable policy"

  statements = [
    "Allow group id ${oci_identity_group.test_operator.id} to manage instance-family in compartment id ${var.compartment_id}",
    "Allow group id ${oci_identity_group.test_operator.id} to use virtual-network-family in compartment id ${var.compartment_id}"
  ]
}

output "test_user_ocid" {
  value = oci_identity_user.test_operator.id
}

output "test_user_api_key_fingerprint" {
  value = oci_identity_api_key.test_operator.fingerprint
}

output "subnet_id" {
  value = oci_core_subnet.public.id
}

output "dynamic_group_id" {
  value = oci_identity_dynamic_group.privileged.id
}

output "tenancy_ocid" {
  value = var.tenancy_ocid
}

output "compartment_id" {
  value = var.compartment_id
}
