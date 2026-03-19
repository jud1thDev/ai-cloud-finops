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

resource "aws_ecr_repository" "ecr-repository-3xy4ow" {
  name                 = "ecr-repository-3xy4ow"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ecr-repository-3xy4ow"
  }
}

resource "aws_ecr_repository" "ecr-repository-qkmgz1" {
  name                 = "ecr-repository-qkmgz1"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ecr-repository-qkmgz1"
  }
}

resource "aws_ecr_repository" "ecr-repository-sj9ege" {
  name                 = "ecr-repository-sj9ege"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ecr-repository-sj9ege"
  }
}

resource "aws_ecr_repository" "ecr-repository-46skvw" {
  name                 = "ecr-repository-46skvw"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ecr-repository-46skvw"
  }
}

resource "aws_ecr_lifecycle_policy" "ecr-repository-46skvw" {
  repository = aws_ecr_repository.ecr-repository-46skvw.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_repository" "ecr-repository-zunqk7" {
  name                 = "ecr-repository-zunqk7"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ecr-repository-zunqk7"
  }
}

resource "aws_ecr_lifecycle_policy" "ecr-repository-zunqk7" {
  repository = aws_ecr_repository.ecr-repository-zunqk7.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

