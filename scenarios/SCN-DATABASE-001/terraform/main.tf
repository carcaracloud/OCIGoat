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

variable "admin_password" {
  type      = string
  sensitive = true
}

resource "oci_database_autonomous_database" "open_by_default" {
  compartment_id = var.compartment_id
  db_name        = "ocigoatdb"
  admin_password = var.admin_password
  db_workload    = "OLTP"
  is_free_tier   = true
}

output "autonomous_database_id" {
  value = oci_database_autonomous_database.open_by_default.id
}

output "connection_urls" {
  value = oci_database_autonomous_database.open_by_default.connection_urls
}
