"""Approximate AWS pricing models (us-east-1 base)."""

from __future__ import annotations

# EC2 On-Demand hourly pricing (USD, us-east-1, Linux)
EC2_HOURLY: dict[str, float] = {
    "t3.micro": 0.0104,
    "t3.small": 0.0208,
    "t3.medium": 0.0416,
    "t3.large": 0.0832,
    "t3.xlarge": 0.1664,
    "m5.large": 0.096,
    "m5.xlarge": 0.192,
    "m5.2xlarge": 0.384,
    "m5.4xlarge": 0.768,
    "m6i.large": 0.096,
    "m6i.xlarge": 0.192,
    "m6i.2xlarge": 0.384,
    "c5.large": 0.085,
    "c5.xlarge": 0.17,
    "c5.2xlarge": 0.34,
    "c6i.large": 0.085,
    "c6i.xlarge": 0.17,
    "r5.large": 0.126,
    "r5.xlarge": 0.252,
    "r5.2xlarge": 0.504,
    "r6g.large": 0.1008,
    "r6g.xlarge": 0.2016,
    "r6g.2xlarge": 0.4032,
    "r6g.4xlarge": 0.8064,
}

# EBS pricing (USD per GB-month)
EBS_GB_MONTH: dict[str, float] = {
    "gp2": 0.10,
    "gp3": 0.08,
    "io1": 0.125,
    "io2": 0.125,
    "st1": 0.045,
    "sc1": 0.015,
    "standard": 0.05,
}

# EBS snapshot pricing
EBS_SNAPSHOT_GB_MONTH = 0.05

# S3 storage pricing (USD per GB-month)
S3_GB_MONTH: dict[str, float] = {
    "STANDARD": 0.023,
    "INTELLIGENT_TIERING": 0.023,
    "STANDARD_IA": 0.0125,
    "ONEZONE_IA": 0.01,
    "GLACIER_INSTANT": 0.004,
    "GLACIER_FLEXIBLE": 0.0036,
    "GLACIER_DEEP": 0.00099,
}

# RDS On-Demand hourly pricing (Multi-AZ multiplier = 2x)
RDS_HOURLY: dict[str, float] = {
    "db.t3.micro": 0.017,
    "db.t3.small": 0.034,
    "db.t3.medium": 0.068,
    "db.r5.large": 0.24,
    "db.r5.xlarge": 0.48,
    "db.r5.2xlarge": 0.96,
    "db.r6g.large": 0.218,
    "db.r6g.xlarge": 0.435,
    "db.r6g.2xlarge": 0.87,
    "db.r6g.4xlarge": 1.74,
}
RDS_MULTI_AZ_MULTIPLIER = 2.0
RDS_BACKUP_GB_MONTH = 0.095  # beyond free tier

# ElastiCache hourly
ELASTICACHE_HOURLY: dict[str, float] = {
    "cache.t3.micro": 0.017,
    "cache.t3.small": 0.034,
    "cache.t3.medium": 0.068,
    "cache.r5.large": 0.228,
    "cache.r5.xlarge": 0.455,
    "cache.r6g.large": 0.206,
}

# Lambda pricing
LAMBDA_REQUEST_PER_MILLION = 0.20
LAMBDA_GB_SECOND = 0.0000166667

# NAT Gateway
NAT_GW_HOURLY = 0.045
NAT_GW_PER_GB = 0.045

# Data transfer
CROSS_AZ_PER_GB = 0.01
INTERNET_EGRESS_PER_GB = 0.09  # first 10TB tier
CLOUDFRONT_PER_GB = 0.085  # US/EU

# Networking
TRANSIT_GW_PER_GB = 0.02
PRIVATELINK_HOURLY_PER_AZ = 0.01
PRIVATELINK_PER_GB = 0.01
VPN_CONNECTION_HOURLY = 0.05

# EIP
EIP_IDLE_HOURLY = 0.005

# ALB/NLB
ALB_HOURLY = 0.0225
NLB_HOURLY = 0.0225
NLB_CROSS_ZONE_PER_GB = 0.01

# Kinesis
KINESIS_SHARD_HOURLY = 0.015
KINESIS_ENHANCED_FANOUT_PER_GB = 0.013
KINESIS_ENHANCED_FANOUT_SHARD_HOURLY = 0.015

# DynamoDB
DYNAMODB_WCU_HOURLY = 0.00065
DYNAMODB_RCU_HOURLY = 0.00013

# SQS
SQS_REQUEST_PER_MILLION = 0.40

# Athena
ATHENA_PER_TB_SCANNED = 5.0

# CloudWatch
CW_CUSTOM_METRIC_MONTH = 0.30
CW_HIGH_RES_METRIC_MONTH = 0.90
CW_LOGS_INGESTION_PER_GB = 0.50
CW_LOGS_STORAGE_PER_GB = 0.03

# ECR
ECR_STORAGE_PER_GB = 0.10

# EKS
EKS_CLUSTER_HOURLY = 0.10

# Fargate pricing (per vCPU-hour and per GB-hour)
FARGATE_VCPU_HOUR = 0.04048
FARGATE_GB_HOUR = 0.004445

# Redshift On-Demand (per node per hour)
REDSHIFT_HOURLY: dict[str, float] = {
    "dc2.large": 0.25,
    "dc2.8xlarge": 4.80,
    "ra3.xlplus": 0.382,
    "ra3.4xlarge": 1.086,
    "ra3.16xlarge": 4.344,
}

# S3 Cross-Region Replication (data transfer out)
S3_CRR_PER_GB = 0.02


def ec2_monthly(instance_type: str, count: int = 1) -> float:
    hourly = EC2_HOURLY.get(instance_type, 0.10)
    return round(hourly * 730 * count, 2)


def ebs_monthly(volume_type: str, size_gb: int, count: int = 1) -> float:
    per_gb = EBS_GB_MONTH.get(volume_type, 0.10)
    return round(per_gb * size_gb * count, 2)


def rds_monthly(
    instance_class: str, multi_az: bool = False, count: int = 1
) -> float:
    hourly = RDS_HOURLY.get(instance_class, 0.24)
    if multi_az:
        hourly *= RDS_MULTI_AZ_MULTIPLIER
    return round(hourly * 730 * count, 2)


def nat_gw_monthly(gb_processed: float, count: int = 1) -> float:
    fixed = NAT_GW_HOURLY * 730 * count
    data = NAT_GW_PER_GB * gb_processed * count
    return round(fixed + data, 2)


def lambda_monthly(
    invocations: int, avg_duration_ms: int, memory_mb: int
) -> float:
    request_cost = (invocations / 1_000_000) * LAMBDA_REQUEST_PER_MILLION
    gb_seconds = invocations * (avg_duration_ms / 1000) * (memory_mb / 1024)
    compute_cost = gb_seconds * LAMBDA_GB_SECOND
    return round(request_cost + compute_cost, 2)
