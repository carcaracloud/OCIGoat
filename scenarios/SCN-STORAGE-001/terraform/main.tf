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

variable "region" {
  type = string
}

data "oci_objectstorage_namespace" "this" {
  compartment_id = var.compartment_id
}

resource "oci_objectstorage_bucket" "leaky" {
  compartment_id = var.compartment_id
  namespace      = data.oci_objectstorage_namespace.this.namespace
  name           = "ocigoat-scn-storage-001-bucket"
  access_type    = "ObjectRead"
}

resource "oci_objectstorage_object" "fixture" {
  bucket    = oci_objectstorage_bucket.leaky.name
  namespace = data.oci_objectstorage_namespace.this.namespace
  object    = "notes/handoff.txt"
  content   = "SCN-STORAGE-001 fixture. Internal handoff notes, temporary link only, do not share."
}

output "namespace" {
  value = data.oci_objectstorage_namespace.this.namespace
}

output "bucket_name" {
  value = oci_objectstorage_bucket.leaky.name
}

output "object_name" {
  value = oci_objectstorage_object.fixture.object
}

output "listing_url" {
  value = "https://objectstorage.${var.region}.oraclecloud.com/n/${data.oci_objectstorage_namespace.this.namespace}/b/${oci_objectstorage_bucket.leaky.name}/o/"
}

output "object_url" {
  value = "https://objectstorage.${var.region}.oraclecloud.com/n/${data.oci_objectstorage_namespace.this.namespace}/b/${oci_objectstorage_bucket.leaky.name}/o/${oci_objectstorage_object.fixture.object}"
}
