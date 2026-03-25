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

resource "aws_instance" "instance-cvi04q" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.medium" # downsized by heuristic
  subnet_id     = aws_subnet.main.id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name = "instance-cvi04q"
  }
}

resource "aws_instance" "instance-2n8q55" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.medium"
  subnet_id     = aws_subnet.main.id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name = "instance-2n8q55"
  }
}

resource "aws_instance" "instance-lh1kos" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.medium"
  subnet_id     = aws_subnet.main.id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name = "instance-lh1kos"
  }
}

# resource "aws_ebs_volume" "ebs-volume-ly10d7" {
#   Removed because it appears unused. Preserve as snapshot if retention is required.
# }

# resource "aws_ebs_volume" "ebs-volume-g1rhjf" {
#   Removed because it appears unused. Preserve as snapshot if retention is required.
# }

# resource "aws_ebs_volume" "ebs-volume-wcp38l" {
#   Removed because it appears unused. Preserve as snapshot if retention is required.
# }