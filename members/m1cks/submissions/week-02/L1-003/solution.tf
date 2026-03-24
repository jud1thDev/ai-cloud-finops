terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_eip" "eip-ej7204" {
  domain   = "vpc"
  instance = aws_instance.running_instance.id
  tags = {
    Name = "eip-ej7204"
  }
}

resource "aws_eip" "eip-j42ph8" {
  domain   = "vpc"
  instance = aws_instance.running_instance.id
  tags = {
    Name = "eip-j42ph8"
  }
}

resource "aws_eip" "eip-kbj2ou" {
  domain   = "vpc"
  instance = aws_instance.running_instance.id
  tags = {
    Name = "eip-kbj2ou"
  }
}