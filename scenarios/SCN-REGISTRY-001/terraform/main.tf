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

resource "oci_artifacts_container_repository" "leaky" {
  compartment_id = var.compartment_id
  display_name   = "ocigoat-scn-registry-001-repo"
  is_public      = true
}

output "repository_id" {
  value = oci_artifacts_container_repository.leaky.id
}

output "repository_name" {
  value = oci_artifacts_container_repository.leaky.display_name
}
