Analyze the following AWS infrastructure for obvious cost waste.

L1 problems are straightforward — look for:
- Stopped/unused EC2 instances (CPU = 0, network = 0)
- Unattached EBS volumes or old snapshots
- Unassociated Elastic IPs
- Idle load balancers (no traffic)
- Resources without lifecycle policies (S3, ECR, CloudWatch Logs)
- Development environments with production-grade configs (Multi-AZ RDS on dev)
- gp2 volumes that should be gp3
- Over-provisioned DynamoDB capacity

Check the metrics summary for resources with:
- zero_pct close to 100% → resource is unused
- Very low mean values → resource is idle
- No variation (trend_pct ≈ 0) → no real workload

Cross-reference with the cost report to see which services have waste.

Remember: NOT all resources are problems. Some are decoys (normal resources). Only flag the ones with clear evidence of waste.

Provide your analysis as JSON:
