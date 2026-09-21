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

variable "instance_shape" {
  type    = string
  default = "VM.Standard.E2.1.Micro"

  validation {
    condition     = contains(["VM.Standard.E2.1.Micro", "VM.Standard.A1.Flex"], var.instance_shape)
    error_message = "Use apenas VM.Standard.E2.1.Micro ou VM.Standard.A1.Flex."
  }
}

variable "instance_ocpus" {
  type    = number
  default = 2

  validation {
    condition     = var.instance_ocpus > 0 && var.instance_ocpus <= 2
    error_message = "instance_ocpus acima de 2 excede o teto Always Free de VM.Standard.A1.Flex."
  }
}

variable "instance_memory_in_gbs" {
  type    = number
  default = 12

  validation {
    condition     = var.instance_memory_in_gbs > 0 && var.instance_memory_in_gbs <= 12
    error_message = "instance_memory_in_gbs acima de 12 excede o teto Always Free de VM.Standard.A1.Flex."
  }
}

variable "availability_domain_name" {
  type    = string
  default = null
}

variable "test_service_port" {
  type    = number
  default = 8080
}

variable "operator_ssh_public_key" {
  type = string
}

variable "flag_content" {
  type    = string
  default = "OCIGOAT{not-tracked}"
}

resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_id
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "ocigoat-scn-net-001-vcn"
  dns_label      = "ocigoatnet1"
}

resource "oci_core_internet_gateway" "this" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-net-001-igw"
  enabled        = true
}

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-net-001-rt-public"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.this.id
  }
}

resource "oci_core_security_list" "restrictive" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-net-001-sl-restrictive"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }
}

resource "oci_core_subnet" "public" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.this.id
  cidr_block                 = "10.0.0.0/24"
  display_name               = "ocigoat-scn-net-001-subnet-public"
  dns_label                  = "public"
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.restrictive.id]
  prohibit_public_ip_on_vnic = false
  prohibit_internet_ingress  = false
}

resource "oci_core_network_security_group" "test_service" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-net-001-nsg"
}

resource "oci_core_network_security_group_security_rule" "allow_test_service" {
  network_security_group_id = oci_core_network_security_group.test_service.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = "0.0.0.0/0"
  source_type               = "CIDR_BLOCK"
  description               = "SCN-NET-001 fixture: acesso ao servico HTTP de teste"

  tcp_options {
    destination_port_range {
      min = var.test_service_port
      max = var.test_service_port
    }
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id

  lifecycle {
    postcondition {
      condition     = length(self.availability_domains) > 0
      error_message = "Nenhum Availability Domain retornado para este compartment/regiao."
    }
  }
}

locals {
  availability_domain_name = coalesce(
    var.availability_domain_name,
    data.oci_identity_availability_domains.ads.availability_domains[0].name
  )
}

data "oci_core_images" "test_image" {
  compartment_id           = var.compartment_id
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"

  lifecycle {
    postcondition {
      condition     = length(self.images) > 0
      error_message = "Nenhuma imagem Oracle Linux 8 encontrada para o shape ${var.instance_shape} nesta regiao/compartment."
    }
  }
}

resource "oci_core_instance" "test_instance" {
  compartment_id      = var.compartment_id
  availability_domain = local.availability_domain_name
  shape               = var.instance_shape
  display_name        = "ocigoat-scn-net-001-instance"

  dynamic "shape_config" {
    for_each = var.instance_shape == "VM.Standard.A1.Flex" ? [1] : []
    content {
      ocpus         = var.instance_ocpus
      memory_in_gbs = var.instance_memory_in_gbs
    }
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public.id
    nsg_ids          = [oci_core_network_security_group.test_service.id]
    assign_public_ip = true
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.test_image.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.operator_ssh_public_key
    user_data = base64encode(<<-EOF
      #cloud-config
      write_files:
        - path: /var/www/scn-net-001/index.html
          content: |
            <html><body><h1>SCN-NET-001 fixture</h1><p>Servico de teste deliberadamente exposto pela NSG.</p><p>${var.flag_content}</p></body></html>
          owner: root:root
          permissions: '0644'
        - path: /etc/systemd/system/scn-net-001-http.service
          content: |
            [Unit]
            Description=SCN-NET-001 test HTTP service
            After=network.target
            [Service]
            WorkingDirectory=/var/www/scn-net-001
            ExecStart=/usr/bin/python3 -m http.server ${var.test_service_port}
            Restart=always
            [Install]
            WantedBy=multi-user.target
      runcmd:
        - systemctl daemon-reload
        - systemctl enable --now scn-net-001-http.service
        - systemctl disable --now firewalld
    EOF
    )
  }
}

data "oci_core_vnic_attachments" "test_instance" {
  compartment_id = var.compartment_id
  instance_id    = oci_core_instance.test_instance.id

  lifecycle {
    postcondition {
      condition     = length(self.vnic_attachments) > 0
      error_message = "Nenhum VNIC attachment encontrado para a instancia."
    }
  }
}

data "oci_core_vnic" "test_instance" {
  vnic_id = data.oci_core_vnic_attachments.test_instance.vnic_attachments[0].vnic_id
}

output "instance_public_ip" {
  value = data.oci_core_vnic.test_instance.public_ip_address
}

output "instance_id" {
  value = oci_core_instance.test_instance.id
}

output "vcn_id" {
  value = oci_core_vcn.this.id
}

output "subnet_id" {
  value = oci_core_subnet.public.id
}

output "security_list_id" {
  value = oci_core_security_list.restrictive.id
}

output "network_security_group_id" {
  value = oci_core_network_security_group.test_service.id
}

output "internet_gateway_id" {
  value = oci_core_internet_gateway.this.id
}

output "route_table_id" {
  value = oci_core_route_table.public.id
}

output "test_service_url" {
  value = "http://${data.oci_core_vnic.test_instance.public_ip_address}:${var.test_service_port}/"
}
