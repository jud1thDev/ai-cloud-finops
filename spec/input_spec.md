# FinOps AI 입력 스펙

학생 AI가 분석을 위해 제공받는 파일 목록과 형식입니다.

## 기본 입력 파일 (모든 레벨)

### 1. `main.tf` — Terraform 인프라 정의
- **형식**: HCL (HashiCorp Configuration Language)
- **내용**: AWS provider 설정 + 리소스 블록들 (문제 리소스 + 디코이 리소스 혼재)
- **주의**: 모든 리소스가 문제인 것은 아님. 정상 리소스(디코이)와 낭비 리소스를 구분해야 함

### 2. `metrics/metrics.json` — CloudWatch 메트릭 시계열
- **형식**: JSON
- **구조**:
  ```json
  {
    "metadata": {
      "scenario_id": "L1-001",
      "period_days": 30,
      "resolution": "hourly",
      "points_per_series": 720
    },
    "resources": {
      "<resource_name>": {
        "resource_type": "aws_instance",
        "is_problem": false,
        "metrics": {
          "<metric_name>": {
            "unit": "Percent",
            "datapoints": [float, ...]
          }
        }
      }
    }
  }
  ```
- **참고**: `is_problem` 필드는 학생에게 제공되지 않음 (채점용으로만 존재)

### 3. `cost_report.json` — 6개월 비용 이력
- **형식**: JSON
- **구조**: 월별 총 비용, 낭비 비용, 서비스별 분류

### 4. `README.md` — 시나리오 컨텍스트
- **형식**: Markdown
- **내용**: 가상 회사 프로필, 배경 설명, 기대 산출물 안내

### 5. `hint.txt` — 힌트 (선택적 참고)
- **형식**: 텍스트
- **내용**: 문제 방향을 암시하는 간략한 힌트

## L2+ 추가 입력 파일

### 6. `business_metrics.json` — 비즈니스 메트릭 (L2+)
- **형식**: JSON
- **구조**:
  ```json
  {
    "daily_metrics": [
      {
        "date": "2026-03-01",
        "requests": 150000,
        "orders": 3200,
        "data_processed_gb": 45.2
      }
    ],
    "current_unit_economics": {
      "cost_per_order": 0.85,
      "cost_per_1k_requests": 2.34,
      "cost_to_revenue_pct": 12.5
    }
  }
  ```

### 7. `tags_inventory.json` — 리소스 태그 인벤토리 (L2+)
- **형식**: JSON
- **구조**: 리소스별 태그 현황, 누락 태그, 커버리지 통계

## L3 추가 입력 파일

### 8. `metrics/cloudwatch_format.json` — AWS GetMetricData 형식 (L3)
- **형식**: JSON (AWS API 응답 형식)
- **구조**: `MetricDataResults[]` 배열, ISO 8601 타임스탬프

### 9. `cur_report.csv` — AWS CUR (Cost and Usage Report) (L3)
- **형식**: CSV
- **컬럼**: `identity/LineItemId`, `lineItem/UsageStartDate`, `lineItem/ProductCode`, `lineItem/UsageType`, `lineItem/UnblendedCost`, `resourceTags/user:Service` 등

### 10. `ri_sp_coverage.json` — RI/SP 커버리지 (L3, rate 카테고리)
- **형식**: JSON
- **구조**: 기존 예약, On-Demand 비율, RI/SP 전환 시 절감 예상

## 출력 스펙

`spec/output_schema.json` 참조. 레벨별 필수 필드:
- **L1**: `analysis.problems_found` + `recommendations` + `summary`
- **L2**: L1 + `analysis.unit_economics`
- **L3**: L2 + `analysis.elasticity` + `alerts`
