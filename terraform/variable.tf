# We use the prefix to make sure all Azure resources get a unique name 
variable "prefix" {
  description = "The prefix used for all resources"
  default = "mlops-sl"
}

# Location variable controls the Azure region. Change it to an allowed region for your account!
variable "location" {
  description = "The Azure Region in which all resources are created."
  default = "norwayeast"
}

# The subscription id defines under which subscription the resources will be created
variable "subscription_id" {
  description = "Azure subscription ID"
  default = ""
}

variable "admin_username" {
  description = "Admin username for the VM"
  default     = "adminuser"
}

variable "ssh_public_key" {
  description = "SSH public key for VM access"
  default     = ""
}

