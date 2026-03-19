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

resource "aws_eip" "eip-u8rypo" {
  domain = "vpc"

  tags = {
    Name = "eip-u8rypo"
  }
}

resource "aws_eip" "eip-9z14li" {
  domain = "vpc"

  tags = {
    Name = "eip-9z14li"
  }
}

resource "aws_eip" "eip-jvpmup" {
  domain = "vpc"

  tags = {
    Name = "eip-jvpmup"
  }
}

resource "aws_eip" "eip-prsvyo" {
  domain = "vpc"

  tags = {
    Name = "eip-prsvyo"
  }
}

resource "aws_eip" "eip-cz0nnu" {
  domain = "vpc"

  tags = {
    Name = "eip-cz0nnu"
  }
}

resource "aws_eip" "eip-ej7204" {
  domain = "vpc"

  instance = aws_instance.running_instance.id

  tags = {
    Name = "eip-ej7204"
  }
}

resource "aws_eip" "eip-j42ph8" {
  domain = "vpc"

  instance = aws_instance.running_instance.id

  tags = {
    Name = "eip-j42ph8"
  }
}

resource "aws_eip" "eip-kbj2ou" {
  domain = "vpc"

  instance = aws_instance.running_instance.id

  tags = {
    Name = "eip-kbj2ou"
  }
}

