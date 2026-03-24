# =============================================================================
# StreamVault — Optimized EBS Snapshot Configuration
# =============================================================================
# OPTIMIZATION SUMMARY:
#   - REMOVED: 200 orphaned EBS snapshots (SourceVolumeStatus = deleted)
#   - RETAINED: 10 active EBS snapshots (SourceVolumeStatus = exists)
#   - ADDED: AWS Data Lifecycle Manager (DLM) policy for automated cleanup
#   - ESTIMATED SAVINGS: ~$100/month (~$1,200/year)
# =============================================================================

# -----------------------------------------------------------------------------
# Retained Active Snapshots (10 of original 210)
# These snapshots have existing source volumes and serve valid backup purposes
# -----------------------------------------------------------------------------

resource "aws_ebs_snapshot" "ebs-snapshot-5uriqp" {
  volume_id   = "vol-5uriqp"
  description = "Active snapshot - source volume exists"

  tags = {
    Name               = "ebs-snapshot-5uriqp"
    SourceVolumeStatus = "exists"
    ManagedBy          = "terraform"
    Environment        = "production"
    RetentionPolicy    = "dlm-managed"
  }
}

resource "aws_ebs_snapshot" "ebs-snapshot-ioofz6" {
  volume_id   = "vol-ioofz6"
  description = "Active snapshot - source volume exists"

  tags = {
    Name               = "ebs-snapshot-ioofz6"
    SourceVolumeStatus = "exists"
    ManagedBy          = "terraform"
    Environment        = "production"
    RetentionPolicy    = "dlm-managed"
  }
}

resource "aws_ebs_snapshot" "ebs-snapshot-tsqw2v" {
  volume_id   = "vol-tsqw2v"
  description = "Active snapshot - source volume exists"

  tags = {
    Name               = "ebs-snapshot-tsqw2v"
    SourceVolumeStatus = "exists"
    ManagedBy          = "terraform"
    Environment        = "production"
    RetentionPolicy    = "dlm-managed"
  }
}

resource "aws_ebs_snapshot" "ebs-snapshot-om0fcd" {
  volume_id   = "vol-om0fcd"
  description = "Active snapshot - source volume exists"

  tags = {
    Name               = "ebs-snapshot-om0fcd"
    SourceVolumeStatus = "exists"
    ManagedBy          = "terraform"
    Environment        = "production"
    RetentionPolicy    = "dlm-managed"
  }
}

resource "aws_ebs_snapshot" "ebs-snapshot-kt4vv8" {
  volume_id   = "vol-kt4vv8"
  description = "Active snapshot - source volume exists"

  tags = {
    Name               = "ebs-snapshot-kt4vv8"
    SourceVolumeStatus = "exists"
    ManagedBy          = "terraform"
    Environment        = "production"
    RetentionPolicy    = "dlm-managed"
  }
}

resource "aws_ebs_snapshot" "ebs-snapshot-jy67h7" {
  volume_id   = "vol-jy67h7"
  description = "Active snapshot - source volume exists"

  tags = {
    Name               = "ebs-snapshot-jy67h7"
    SourceVolumeStatus = "exists"
    ManagedBy          = "terraform"
    Environment        = "production"
    RetentionPolicy    = "dlm-managed"
  }
}

resource "aws_ebs_snapshot" "ebs-snapshot-kuqbtk" {
  volume_id   = "vol-kuqbtk"
  description = "Active snapshot - source volume exists"

  tags = {
    Name               = "ebs-snapshot-kuqbtk"
    SourceVolumeStatus = "exists"
    ManagedBy          = "terraform"
    Environment        = "production"
    RetentionPolicy    = "dlm-managed"
  }
}

resource "aws_ebs_snapshot" "ebs-snapshot-dih1z2" {
  volume_id   = "vol-dih1z2"
  description = "Active snapshot - source volume exists"

  tags = {
    Name               = "ebs-snapshot-dih1z2"
    SourceVolumeStatus = "exists"
    ManagedBy          = "terraform"
    Environment        = "production"
    RetentionPolicy    = "dlm-managed"
  }
}

resource "aws_ebs_snapshot" "ebs-snapshot-9b4v5e" {
  volume_id   = "vol-9b4v5e"
  description = "Active snapshot - source volume exists"

  tags = {
    Name               = "ebs-snapshot-9b4v5e"
    SourceVolumeStatus = "exists"
    ManagedBy          = "terraform"
    Environment        = "production"
    RetentionPolicy    = "dlm-managed"
  }
}

resource "aws_ebs_snapshot" "ebs-snapshot-7nucp1" {
  volume_id   = "vol-7nucp1"
  description = "Active snapshot - source volume exists"

  tags = {
    Name               = "ebs-snapshot-7nucp1"
    SourceVolumeStatus = "exists"
    ManagedBy          = "terraform"
    Environment        = "production"
    RetentionPolicy    = "dlm-managed"
  }
}

# -----------------------------------------------------------------------------
# AWS Data Lifecycle Manager (DLM) — Automated Snapshot Lifecycle Policy
# Prevents future accumulation of orphaned snapshots
# -----------------------------------------------------------------------------

resource "aws_iam_role" "dlm_lifecycle_role" {
  name = "streamvault-dlm-lifecycle-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "dlm.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name      = "streamvault-dlm-lifecycle-role"
    ManagedBy = "terraform"
    Purpose   = "DLM snapshot lifecycle management"
  }
}

resource "aws_iam_role_policy" "dlm_lifecycle_policy" {
  name = "streamvault-dlm-lifecycle-policy"
  role = aws_iam_role.dlm_lifecycle_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateSnapshot",
          "ec2:CreateSnapshots",
          "ec2:DeleteSnapshot",
          "ec2:DescribeInstances",
          "ec2:DescribeVolumes",
          "ec2:DescribeSnapshots",
          "ec2:EnableFastSnapshotRestores",
          "ec2:DisableFastSnapshotRestores",
          "ec2:CreateTags",
          "ec2:DeleteTags"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_dlm_lifecycle_policy" "snapshot_lifecycle" {
  description        = "StreamVault EBS snapshot lifecycle policy - auto-cleanup"
  execution_role_arn = aws_iam_role.dlm_lifecycle_role.arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["VOLUME"]

    schedule {
      name = "Daily snapshots with 30-day retention"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["03:00"]
      }

      retain_rule {
        count = 30
      }

      tags_to_add = {
        SnapshotCreator = "DLM"
        ManagedBy       = "terraform"
      }

      copy_tags = true
    }

    target_tags = {
      Backup = "true"
    }
  }

  tags = {
    Name        = "streamvault-snapshot-lifecycle"
    ManagedBy   = "terraform"
    Environment = "production"
    Purpose     = "Prevent orphaned snapshot accumulation"
  }
}

# =============================================================================
# REMOVED RESOURCES (200 orphaned snapshots) — DO NOT RE-ADD
# =============================================================================
# The following 200 snapshots were removed because their source EBS volumes
# have been deleted. They served no operational purpose and cost ~$100/month.
#
# Examples of removed snapshots:
#   - ebs-snapshot-kb8fyl (SourceVolumeStatus: deleted, ~2,097 storage)
#   - ebs-snapshot-ximjut (SourceVolumeStatus: deleted, ~2,007 storage)
#   - ebs-snapshot-ykdgc2 (SourceVolumeStatus: deleted, ~1,966 storage)
#   - ebs-snapshot-6vnfj0 (SourceVolumeStatus: deleted, ~1,987 storage)
#   - ... and 196 more orphaned snapshots
#
# Total removed: 200 aws_ebs_snapshot resources
# Total savings: ~$100/month ($1,200/year)
#
# Before applying this configuration:
#   1. Verify no AMIs or launch templates reference these snapshots
#   2. Run: terraform plan -out=cleanup.plan
#   3. Review the plan carefully
#   4. Run: terraform apply cleanup.plan
# =============================================================================