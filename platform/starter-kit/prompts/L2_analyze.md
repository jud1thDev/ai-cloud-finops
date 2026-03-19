Analyze the following AWS infrastructure for cost optimization. This is an L2 problem requiring pattern analysis.

L2 problems require looking at metric patterns over time:
- Lambda functions with memory/timeout set much higher than actual usage
- ECS/Fargate tasks with over-provisioned vCPU/memory
- Auto Scaling groups with missing warm-up causing over-scaling
- Kinesis streams with too many shards for actual throughput
- ElastiCache/RDS with more capacity than needed
- SQS without long polling (high empty receive costs)
- CloudWatch metrics at unnecessary high resolution

Analyze the metrics summary:
- Compare mean vs max — if max is much lower than provisioned, it's overprovisioned
- Look for resources where utilization is consistently low (<30%)
- Check trend — degrading efficiency means growing waste

You also have BUSINESS METRICS. Calculate and include unit economics:
- cost_per_order: monthly_cost / total_orders
- cost_per_1k_requests: monthly_cost / (total_requests / 1000)
- trend: "improving" if cost/unit is decreasing, "degrading" if increasing
- vs_previous_period: percentage change from previous period

Your JSON output MUST include `analysis.unit_economics` with these fields.

Provide your analysis as JSON:
