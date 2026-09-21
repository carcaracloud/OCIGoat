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

variable "target_ssh_public_key" {
  type = string
}

variable "flag_content" {
  type    = string
  default = "OCIGOAT{not-tracked}"
}

resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_id
  cidr_blocks    = ["10.6.0.0/16"]
  display_name   = "ocigoat-scn-bastion-001-vcn"
  dns_label      = "ocigoatbast1"
}

resource "oci_core_security_list" "ssh_from_vcn" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-bastion-001-sl"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  ingress_security_rules {
    source   = "10.6.0.0/24"
    protocol = "6"

    tcp_options {
      min = 22
      max = 22
    }
  }
}

resource "oci_core_subnet" "private" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.this.id
  cidr_block                 = "10.6.0.0/24"
  display_name               = "ocigoat-scn-bastion-001-subnet-private"
  dns_label                  = "private"
  security_list_ids          = [oci_core_security_list.ssh_from_vcn.id]
  prohibit_public_ip_on_vnic = true
  prohibit_internet_ingress  = true
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

data "oci_core_images" "target_image" {
  compartment_id           = var.compartment_id
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = "VM.Standard.E2.1.Micro"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "target" {
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  shape               = "VM.Standard.E2.1.Micro"
  display_name        = "ocigoat-scn-bastion-001-target"

  create_vnic_details {
    subnet_id        = oci_core_subnet.private.id
    assign_public_ip = false
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.target_image.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.target_ssh_public_key
    user_data = base64encode(<<-EOF
      #cloud-config
      write_files:
        - path: /home/opc/flag.txt
          content: |
            ${var.flag_content}
          owner: opc:opc
          permissions: '0644'
    EOF
    )
  }
}

resource "oci_bastion_bastion" "this" {
  compartment_id               = var.compartment_id
  bastion_type                 = "STANDARD"
  target_subnet_id             = oci_core_subnet.private.id
  name                         = "ocigoat-scn-bastion-001"
  client_cidr_block_allow_list = ["0.0.0.0/0"]
}

resource "oci_identity_group" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-bastion-001-operator"
  description    = "SCN-BASTION-001 test group"
}

resource "oci_identity_user" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-bastion-001-operator"
  description    = "SCN-BASTION-001 test user"
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
  name           = "ocigoat-scn-bastion-001-operator-policy"
  description    = "SCN-BASTION-001 fixture policy"

  statements = [
    "Allow group id ${oci_identity_group.test_operator.id} to manage bastion-session in compartment id ${var.compartment_id}",
    "Allow group id ${oci_identity_group.test_operator.id} to use bastion in compartment id ${var.compartment_id}",
    "Allow group id ${oci_identity_group.test_operator.id} to read instance-family in compartment id ${var.compartment_id}",
    "Allow group id ${oci_identity_group.test_operator.id} to read virtual-network-family in compartment id ${var.compartment_id}"
  ]
}

output "bastion_id" {
  value = oci_bastion_bastion.this.id
}

output "target_id" {
  value = oci_core_instance.target.id
}

output "target_private_ip" {
  value = oci_core_instance.target.private_ip
}

output "test_user_ocid" {
  value = oci_identity_user.test_operator.id
}

output "test_user_api_key_fingerprint" {
  value = oci_identity_api_key.test_operator.fingerprint
}
