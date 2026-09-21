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

variable "operator_ssh_public_key" {
  type = string
}

variable "flag_content" {
  type    = string
  default = "OCIGOAT{not-tracked}"
}

resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_id
  cidr_blocks    = ["10.5.0.0/16"]
  display_name   = "ocigoat-scn-net-002-vcn"
  dns_label      = "ocigoatnet2"
}

resource "oci_core_internet_gateway" "this" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-net-002-igw"
  enabled        = true
}

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-net-002-rt-public"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.this.id
  }
}

resource "oci_core_security_list" "ssh" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-net-002-sl-ssh"

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
  cidr_block                 = "10.5.0.0/24"
  display_name               = "ocigoat-scn-net-002-subnet"
  dns_label                  = "public"
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.ssh.id]
  prohibit_public_ip_on_vnic = false
  prohibit_internet_ingress  = false
}

resource "oci_core_network_security_group" "trusted" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-net-002-nsg-trusted"
}

resource "oci_core_network_security_group" "protected" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-net-002-nsg-protected"
}

resource "oci_core_network_security_group" "incidental" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "ocigoat-scn-net-002-nsg-incidental"
}

resource "oci_core_network_security_group_security_rule" "protected_allow_trusted" {
  network_security_group_id = oci_core_network_security_group.protected.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = oci_core_network_security_group.trusted.id
  source_type               = "NETWORK_SECURITY_GROUP"

  tcp_options {
    destination_port_range {
      min = 8080
      max = 8080
    }
  }
}

resource "oci_core_network_security_group_security_rule" "incidental_allow_trusted" {
  network_security_group_id = oci_core_network_security_group.incidental.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = oci_core_network_security_group.trusted.id
  source_type               = "NETWORK_SECURITY_GROUP"

  tcp_options {
    destination_port_range {
      min = 3000
      max = 3000
    }
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

data "oci_core_images" "test_image" {
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
  display_name        = "ocigoat-scn-net-002-target"

  create_vnic_details {
    subnet_id        = oci_core_subnet.public.id
    nsg_ids          = [oci_core_network_security_group.protected.id, oci_core_network_security_group.incidental.id]
    assign_public_ip = false
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.test_image.images[0].id
  }

  metadata = {
    user_data = base64encode(<<-EOF
      #cloud-config
      write_files:
        - path: /tmp/index.html
          content: |
            <html><body><h1>SCN-NET-002 protected fixture</h1><p>${var.flag_content}</p></body></html>
          owner: root:root
          permissions: '0644'
        - path: /etc/systemd/system/scn-net-002-protected.service
          content: |
            [Unit]
            Description=SCN-NET-002 protected service
            After=network.target
            [Service]
            WorkingDirectory=/tmp
            ExecStart=/usr/bin/python3 -m http.server 8080
            Restart=always
            [Install]
            WantedBy=multi-user.target
        - path: /etc/systemd/system/scn-net-002-incidental.service
          content: |
            [Unit]
            Description=SCN-NET-002 incidental service
            After=network.target
            [Service]
            WorkingDirectory=/tmp
            ExecStart=/usr/bin/python3 -m http.server 3000
            Restart=always
            [Install]
            WantedBy=multi-user.target
      runcmd:
        - systemctl daemon-reload
        - systemctl enable --now scn-net-002-protected.service
        - systemctl enable --now scn-net-002-incidental.service
        - systemctl disable --now firewalld
    EOF
    )
  }
}

resource "oci_core_instance" "prober" {
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  shape               = "VM.Standard.E2.1.Micro"
  display_name        = "ocigoat-scn-net-002-prober"

  create_vnic_details {
    subnet_id        = oci_core_subnet.public.id
    nsg_ids          = [oci_core_network_security_group.trusted.id]
    assign_public_ip = true
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.test_image.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.operator_ssh_public_key
  }
}

data "oci_core_vnic_attachments" "target" {
  compartment_id = var.compartment_id
  instance_id    = oci_core_instance.target.id
}

data "oci_core_vnic" "target" {
  vnic_id = data.oci_core_vnic_attachments.target.vnic_attachments[0].vnic_id
}

data "oci_core_vnic_attachments" "prober" {
  compartment_id = var.compartment_id
  instance_id    = oci_core_instance.prober.id
}

data "oci_core_vnic" "prober" {
  vnic_id = data.oci_core_vnic_attachments.prober.vnic_attachments[0].vnic_id
}

output "target_private_ip" {
  value = data.oci_core_vnic.target.private_ip_address
}

output "prober_public_ip" {
  value = data.oci_core_vnic.prober.public_ip_address
}
