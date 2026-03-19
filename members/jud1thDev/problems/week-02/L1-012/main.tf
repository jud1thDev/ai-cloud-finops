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

resource "aws_s3_bucket" "s3-bucket-69hmk4" {
  bucket = "app-assets-prod"

  tags = {
    Name        = "app-assets-prod"
  }
}

resource "aws_s3_bucket_versioning" "s3-bucket-69hmk4" {
  bucket = aws_s3_bucket.s3-bucket-69hmk4.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "s3-bucket-yg11le" {
  bucket = "app-assets-staging"

  tags = {
    Name        = "app-assets-staging"
  }
}

resource "aws_s3_bucket_versioning" "s3-bucket-yg11le" {
  bucket = aws_s3_bucket.s3-bucket-yg11le.id

  versioning_configuration {
    status = "Enabled"
  }
}

