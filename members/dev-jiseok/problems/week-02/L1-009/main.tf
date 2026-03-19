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

resource "aws_ecr_repository" "ecr-repository-o362uj" {
  name                 = "ecr-repository-o362uj"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ecr-repository-o362uj"
  }
}

resource "aws_ecr_repository" "ecr-repository-fx1xce" {
  name                 = "ecr-repository-fx1xce"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ecr-repository-fx1xce"
  }
}

resource "aws_ecr_repository" "ecr-repository-t2flin" {
  name                 = "ecr-repository-t2flin"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ecr-repository-t2flin"
  }
}

resource "aws_ecr_repository" "ecr-repository-74u788" {
  name                 = "ecr-repository-74u788"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ecr-repository-74u788"
  }
}

resource "aws_ecr_lifecycle_policy" "ecr-repository-74u788" {
  repository = aws_ecr_repository.ecr-repository-74u788.name

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

resource "aws_ecr_repository" "ecr-repository-rxw8pd" {
  name                 = "ecr-repository-rxw8pd"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ecr-repository-rxw8pd"
  }
}

resource "aws_ecr_lifecycle_policy" "ecr-repository-rxw8pd" {
  repository = aws_ecr_repository.ecr-repository-rxw8pd.name

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

