Analyze the following AWS infrastructure for comprehensive cost optimization. This is an L3 problem requiring architecture-level analysis.

L3 problems involve:
- Network cost issues (NAT Gateway routing, Transit Gateway overhead, missing VPC Endpoints)
- RI/SP coverage gaps (high on-demand spend, mismatched reserved instance families)
- Tagging governance failures (unallocated spend from untagged resources)
- Data architecture waste (full table scans, unnecessary replication, always-on clusters)
- Multi-account consolidation opportunities

Analyze ALL provided data sources:
1. Terraform: Look for architectural anti-patterns
2. Metrics: Identify usage patterns (peak vs off-peak, seasonal)
3. Cost report: Track waste trends over 6 months
4. Business metrics: Calculate unit economics and efficiency trends
5. Tags inventory: Find non-compliant resources and unallocated spend
6. RI/SP coverage: Calculate savings from better reservation strategy
7. CUR report: Identify top cost drivers by service
8. CloudWatch format: Detect anomalies in time series

Your JSON output MUST include ALL of these:
- `analysis.problems_found[]` — all identified issues
- `analysis.unit_economics` — cost efficiency metrics
- `analysis.elasticity` — infrastructure elasticity score (0-100) and detail
- `recommendations[]` — prioritized action items
- `alerts[]` — notifications that should be sent (channel, urgency, title, message, severity)
- `summary` — totals and confidence score

For alerts, generate realistic notifications:
- Slack alerts for cost anomalies and efficiency degradation
- Email alerts for RI/SP coverage gaps
- Critical alerts for unused high-cost resources

Provide your analysis as JSON:
