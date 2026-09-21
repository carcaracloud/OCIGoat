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

variable "flag_content" {
  type    = string
  default = "OCIGOAT{not-tracked}"
}

resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_id
  cidr_blocks    = ["10.7.0.0/16"]
  display_name   = "ocigoat-scn-compute-001-vcn"
  dns_label      = "ocigoatcomp1"
}

resource "oci_core_internet_gateway" "this" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-compute-001-igw"
  enabled        = true
}

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-compute-001-rt-public"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.this.id
  }
}

resource "oci_core_security_list" "ssh" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-compute-001-sl"

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
  cidr_block                 = "10.7.0.0/24"
  display_name               = "ocigoat-scn-compute-001-subnet"
  dns_label                  = "public"
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.ssh.id]
  prohibit_public_ip_on_vnic = false
  prohibit_internet_ingress  = false
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

data "oci_core_images" "source_image" {
  compartment_id           = var.compartment_id
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = "VM.Standard.E2.1.Micro"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "source" {
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  shape               = "VM.Standard.E2.1.Micro"
  display_name        = "ocigoat-scn-compute-001-source"

  create_vnic_details {
    subnet_id        = oci_core_subnet.public.id
    assign_public_ip = false
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.source_image.images[0].id
  }

  metadata = {
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

data "oci_objectstorage_namespace" "this" {
  compartment_id = var.compartment_id
}

resource "oci_objectstorage_bucket" "exfil" {
  compartment_id = var.compartment_id
  namespace      = data.oci_objectstorage_namespace.this.namespace
  name           = "ocigoat-scn-compute-001-image-export"
}

resource "oci_identity_group" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-compute-001-operator"
  description    = "SCN-COMPUTE-001 test group"
}

resource "oci_identity_user" "test_operator" {
  compartment_id = var.tenancy_ocid
  name           = "ocigoat-scn-compute-001-operator"
  description    = "SCN-COMPUTE-001 test user"
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
  name           = "ocigoat-scn-compute-001-operator-policy"
  description    = "SCN-COMPUTE-001 vulnerable policy"

  statements = [
    "Allow group id ${oci_identity_group.test_operator.id} to manage instance-family in compartment id ${var.compartment_id}",
    "Allow group id ${oci_identity_group.test_operator.id} to manage object-family in compartment id ${var.compartment_id}"
  ]
}

output "source_instance_id" {
  value = oci_core_instance.source.id
}

output "namespace" {
  value = data.oci_objectstorage_namespace.this.namespace
}

output "bucket_name" {
  value = oci_objectstorage_bucket.exfil.name
}

output "test_user_ocid" {
  value = oci_identity_user.test_operator.id
}

output "test_user_api_key_fingerprint" {
  value = oci_identity_api_key.test_operator.fingerprint
}
