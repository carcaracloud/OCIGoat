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

variable "kubernetes_version" {
  type = string
}

resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_id
  cidr_blocks    = ["10.2.0.0/16"]
  display_name   = "ocigoat-scn-oke-001-vcn"
  dns_label      = "ocigoatoke1"
}

resource "oci_core_internet_gateway" "this" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-oke-001-igw"
  enabled        = true
}

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-oke-001-rt-public"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.this.id
  }
}

resource "oci_core_security_list" "endpoint" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-oke-001-sl-endpoint"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"

    tcp_options {
      min = 6443
      max = 6443
    }
  }
}

resource "oci_core_subnet" "endpoint" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.this.id
  cidr_block                 = "10.2.0.0/24"
  display_name               = "ocigoat-scn-oke-001-subnet-endpoint"
  dns_label                  = "endpoint"
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.endpoint.id]
  prohibit_public_ip_on_vnic = false
  prohibit_internet_ingress  = false
}

resource "oci_containerengine_cluster" "vulnerable" {
  compartment_id     = var.compartment_id
  kubernetes_version = var.kubernetes_version
  name               = "ocigoat-scn-oke-001-cluster"
  vcn_id             = oci_core_vcn.this.id
  type               = "BASIC_CLUSTER"

  endpoint_config {
    is_public_ip_enabled = true
    subnet_id            = oci_core_subnet.endpoint.id
  }
}

output "cluster_id" {
  value = oci_containerengine_cluster.vulnerable.id
}
