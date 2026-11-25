terraform {
  required_version = ">= 1.3"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    formal = {
      source  = "formalco/formal"
      version = ">= 4.46.0"
    }
  }
}
