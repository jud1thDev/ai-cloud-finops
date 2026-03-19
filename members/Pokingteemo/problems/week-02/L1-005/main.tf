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

resource "aws_lb" "lb-e7wr3x" {
  name               = "lb-e7wr3x"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb-e7wr3x_sg.id]
  subnets = var.public_subnet_ids

  tags = {
    Name = "lb-e7wr3x"
  }
}

resource "aws_lb" "lb-fs75b7" {
  name               = "lb-fs75b7"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb-fs75b7_sg.id]
  subnets = var.public_subnet_ids

  tags = {
    Name = "lb-fs75b7"
  }
}

resource "aws_lb" "lb-3a0ka5" {
  name               = "lb-3a0ka5"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb-3a0ka5_sg.id]
  subnets = var.public_subnet_ids

  tags = {
    Name = "lb-3a0ka5"
  }
}

