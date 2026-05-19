# Configure the Azure provider
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.1.0"
    }
  }
  required_version = ">= 1.1.0"
}

provider "azurerm" {
  # use subscription_id from variables
  features {}
  subscription_id = var.subscription_id
}

# Resource group — container for all resources
resource "azurerm_resource_group" "mlops-resource" {
  name     = "${var.prefix}-resource-group"
  location = var.location
}


# Virtual network — private network for the VM
resource "azurerm_virtual_network" "main" {
  address_space = ["10.0.0.0/16"]
  name = "${var.prefix}-vnet"
  location = azurerm_resource_group.mlops-resource.location
  resource_group_name = azurerm_resource_group.mlops-resource.name
}

# Subnet — subdivision of the virtual network, 24 means 256 different addresses of this subnet
resource "azurerm_subnet" "main" {
  address_prefixes = ["10.0.1.0/24"]
  name = "${var.prefix}-snet"
  resource_group_name = azurerm_resource_group.mlops-resource.name
  virtual_network_name = azurerm_virtual_network.main.name
}

# Public IP - so you can reach the VM from outside
resource "azurerm_public_ip" "main" {
  # dynamic allocation
  name = "${var.prefix}-public-ip"
  location = azurerm_resource_group.mlops-resource.location
  resource_group_name = azurerm_resource_group.mlops-resource.name
  allocation_method = "Static" # Azure reserves fixed ip adress (stays the same if u start/stop VM)
}

# Network security group — firewall rules
resource "azurerm_network_security_group" "main" {
    name                = "${var.prefix}-nsg"
    location            = azurerm_resource_group.mlops-resource.location
    resource_group_name = azurerm_resource_group.mlops-resource.name
  # rule: allow SSH port 22
    security_rule {
        name                       = "allow-ssh"
        priority                   = 100 # If rule 100 matches the traffic, Azure applies it and stops checking. Rule 200 never gets checked for that packet.
        direction                  = "Inbound" # Traffic coming into the VM
        access                     = "Allow" 
        protocol                   = "Tcp"
        source_port_range          = "*" # Allow any ports (f.e laptop pick temporary port on own side)
        destination_port_range     = "22" #SSH port on VM
        source_address_prefix      = "*" # Allow traffic from any ip in the world (in prod would restric this)
        destination_address_prefix = "*" # No matter what IP arrives to VM apply this rule
    }

  # Allow Flask API - our prediction endpoint
  # This is what external users call to get predictions
  security_rule {
    name                       = "allow-api"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3001"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow MLflow UI - experiment tracking dashboard
  # Used to view metrics, model versions, artifacts
  security_rule {
    name                       = "allow-mlflow"
    priority                   = 300
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5000"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow MinIO API - object storage S3-compatible endpoint
  # MLflow uses this internally to store model artifacts
  security_rule {
    name                       = "allow-minio"
    priority                   = 400
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "9000"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow MinIO Console - web UI for browsing stored objects
  # Used to verify model pickle files are being saved correctly
  security_rule {
    name                       = "allow-minio-console"
    priority                   = 500
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "9001"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

}

# Network interface — connects VM to the network(connect subney and public ip)
resource "azurerm_network_interface" "main" {
  name                = "${var.prefix}-nic"
  location            = azurerm_resource_group.mlops-resource.location
  resource_group_name = azurerm_resource_group.mlops-resource.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.main.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.main.id
  }
}


# Associate security group with network interface (apply the firewall rules to to the VM network)
resource "azurerm_network_interface_security_group_association" "main" {
  network_interface_id      = azurerm_network_interface.main.id
  network_security_group_id = azurerm_network_security_group.main.id
}

# The VM itself
resource "azurerm_linux_virtual_machine" "main" {
    name                = "${var.prefix}-VM"
    location            = azurerm_resource_group.mlops-resource.location
    resource_group_name = azurerm_resource_group.mlops-resource.name  # size: Standard_B2s

    # Size of vm 
    size = "Standard_B2s_v2"

    # admin username from variable
    admin_username = var.admin_username

  # SSH key from variable
    admin_ssh_key {
    username   = var.admin_username
    public_key = var.ssh_public_key
    }

    # attach network interface
    network_interface_ids = [azurerm_network_interface.main.id]

    os_disk {
    caching              = "ReadWrite" # 
    storage_account_type = "Standard_LRS" # Cheapest
    }

    # Get latest ubuntu for the VM
    source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
    }
    
    # custom_data: base64 encoded startup script
    custom_data = base64encode(<<-EOF
    #!/bin/bash
    
    # 1 update package list
    apt-get update -y

    # 2 install docker dependencies
    apt-get install -y ca-certificates curl gnupg git

    # 3 add docker GPG key and repository
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y

    # 4 install docker
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # 5 add adminuser to docker group so they can run docker without sudo
    usermod -aG docker adminuser

    # 6 start docker service
    systemctl enable docker
    systemctl start docker

    # 7 clone your github repo
    git clone https://github.com/RobertI321/ml-ops-sl-project.git /home/adminuser/app

    # 8 print done
    echo "Setup complete" >> /var/log/startup.log
    EOF
    )

}

# Output the public IP so you know where to connect
output "public_ip" {
  value = azurerm_public_ip.main.ip_address
}