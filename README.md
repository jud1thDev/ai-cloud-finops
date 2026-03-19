# FinOps AI Study Platform

FinOps(클라우드 비용 최적화) AI 에이전트를 훈련/평가하기 위한 **시뮬레이션 문제 자동 출제 + 자동 채점 플랫폼**.

AWS 인프라의 비용 낭비 시나리오를 Terraform + 메트릭 + 비용 리포트 + 비즈니스 메트릭 + CUR 데이터로 생성하고, 학생 AI가 구조화된 분석 결과를 출력하면 다차원 자동 채점합니다.

> 우아한형제들 FinOps 기술블로그 수준의 실무 시나리오를 지향합니다.
> (단위경제 KPI, 탄력성 지표, 비용 이상탐지, RI/SP 전략)

## 전체 구조

```
학생 AI 에이전트
    │
    │  finops-study pull --week 4       ← 문제 다운로드
    ▼
┌─────────────────────────────────┐
│  입력 파일 (레벨별 점진 확장)      │
│  main.tf                        │  ← 항상
│  metrics/metrics.json           │  ← 항상
│  cost_report.json               │  ← 항상
│  business_metrics.json          │  ← L2+
│  tags_inventory.json            │  ← L2+
│  metrics/cloudwatch_format.json │  ← L3
│  cur_report.csv                 │  ← L3
│  ri_sp_coverage.json            │  ← L3 (rate 카테고리)
└─────────────────────────────────┘
    │
    │  AI 분석 → spec/output_schema.json 형식으로 출력
    ▼
┌─────────────────────────────────┐
│  출력: analysis.json             │
│  ├ analysis.problems_found[]    │  ← L1+ (필수)
│  ├ analysis.unit_economics      │  ← L2+ (필수)
│  ├ analysis.elasticity          │  ← L3  (필수)
│  ├ recommendations[]            │  ← L1+ (필수)
│  ├ alerts[]                     │  ← L3  (필수)
│  ├ optimized_terraform          │  ← 선택
│  └ summary                      │  ← L1+ (필수)
└─────────────────────────────────┘
    │
    │  finops-study submit --week 4 --scenario L2-014
    ▼
┌─────────────────────────────────┐
│  자동 채점 (6차원)               │
│  Schema 유효성        10점       │
│  Resource 식별 정확도  30점       │
│  Terraform 수정 품질   15점       │
│  Savings 추정 정확도   20점       │
│  Unit Economics (L2+)  15점       │
│  Alerts 생성 (L3)      10점       │
│  ─────────────────────────       │
│  합계: 100점 (레벨별 정규화)      │
└─────────────────────────────────┘
```

## 무엇을 하는 프로젝트인가

```
시나리오 선택 → 가상 회사 생성 → 8종 데이터 파일 생성 → 정답지 + 채점표 생성
```

예를 들어 "L1-001: 중지된 EC2 미삭제" 시나리오를 실행하면:

| 생성 파일 | 내용 |
|-----------|------|
| `main.tf` | stopped EC2 + gp2 EBS 3개 + 정상 인스턴스 2개 (decoy) |
| `metrics/metrics.json` | 30일간 시간별 CPU/네트워크/IOPS 시계열 |
| `cost_report.json` | 6개월 비용 히스토리 + 서비스별 breakdown |
| `business_metrics.json` | 30일 일별 트래픽 + 단위경제 지표 (L2+) |
| `tags_inventory.json` | 리소스별 태그 감사 결과 (L2+) |
| `metrics/cloudwatch_format.json` | AWS GetMetricData API 형식 (L3) |
| `cur_report.csv` | AWS CUR 표준 포맷 CSV (L3) |
| `ri_sp_coverage.json` | RI/SP 커버리지 분석 (L3, rate 카테고리) |
| `README.md` | 가상 회사 배경 + 과제 설명 |
| `hint.txt` | 방향성 힌트 |
| `answer.json` | 정답 (문제 요약, 원인, 권장 조치, 절감액, 증거) |
| `scoring_rubric.json` | 채점 기준 |

## 시나리오 카탈로그

총 **40개** 시나리오가 3단계 난이도로 구성되어 있습니다.

### L1 — 명시적 문제 (13개)
Cost Explorer / Trusted Advisor에서 바로 보이는 수준.

| ID | 시나리오 | 월 낭비 |
|----|---------|---------|
| L1-001 | 중지된 EC2에 EBS 볼륨 과금 | $150 |
| L1-002 | gp2 EBS 볼륨 미전환 | $40 |
| L1-003 | 비연결 Elastic IP | $18 |
| L1-004 | 개발 환경 RDS Multi-AZ | $350 |
| L1-005 | 사용 안 하는 Load Balancer | $33 |
| L1-006 | CloudWatch Logs 영구 보존 | $144 |
| L1-007 | 오래된 EBS 스냅샷 방치 | $100 |
| L1-008 | 미사용 AMI + 연결 스냅샷 | $30 |
| L1-009 | ECR 이미지 Lifecycle 없음 | $20 |
| L1-010 | DynamoDB 프로비전드 용량 과잉 | $522 |
| L1-011 | S3 Lifecycle 정책 없음 | $152 |
| L1-012 | S3 버전 관리 + 이전 버전 미정리 | $230 |
| L1-013 | RDS 백업 보존 기간 35일 | $266 |

### L2 — 패턴형 문제 (11개)
CloudWatch 메트릭을 일정 기간 분석해야 발견. 단위경제 분석 필요.

| ID | 시나리오 | 월 낭비 |
|----|---------|---------|
| L2-014 | Lambda 메모리 과잉 할당 | $750 |
| L2-015 | Lambda 타임아웃 과잉 설정 | $360 |
| L2-016 | ECS Fargate vCPU/메모리 과잉 | $1,050 |
| L2-017 | Auto Scaling warm-up 미설정 | $420 |
| L2-018 | Kinesis Shard 정적 과잉 | $985 |
| L2-019 | ElastiCache 노드 과잉 | $665 |
| L2-020 | RDS Read Replica 미사용 | $1,051 |
| L2-021 | SQS Long Polling 미설정 | $120 |
| L2-022 | Kinesis Enhanced Fan-Out 불필요 | $437 |
| L2-023 | Athena 결과 S3 무제한 저장 | $115 |
| L2-024 | CloudWatch 메트릭 1초 해상도 | $120 |

### L3 — 아키텍처형 문제 (16개)
멀티소스 로그 상관분석 + 설계 리뷰 + RI/SP 전략 필요.

| ID | 시나리오 | 월 낭비 |
|----|---------|---------|
| L3-025 | NAT Gateway Single-AZ 배치 | $66 |
| L3-026 | Transit Gateway 불필요 경유 | $200 |
| L3-027 | PrivateLink Interface Endpoint 남발 | $144 |
| L3-028 | NLB Cross-Zone 고비용 전송 | $400 |
| L3-029 | S3를 NAT 경유 접근 | $360 |
| L3-030 | VPN + Direct Connect 동시 유지 | $73 |
| L3-031 | 태그 없는 리소스 50% | $5,000 |
| L3-032 | Reserved Instance 패밀리 미스매치 | $1,402 |
| L3-033 | Savings Plan Coverage Gap | $1,200 |
| L3-034 | 멀티 계정 미통합 | $3,000 |
| L3-035 | Athena 파티셔닝 없는 대형 테이블 | $7,500 |
| L3-036 | Redshift 24/7 Always-On | $782 |
| L3-037 | S3 Cross-Region Replication 전체 적용 | $368 |
| L3-038 | EKS Pod resource request 과잉 | $3,360 |
| L3-039 | CloudFront 없이 S3 Direct Egress | $270 |
| L3-040 | RDS Proxy 없는 Lambda→RDS 연결 | $515 |

## 설치

```bash
# 기본 설치
pip install -e ".[dev]"

# 채점 기능 포함 (jsonschema)
pip install -e ".[dev,scoring]"

# Claude API 연동 포함
pip install -e ".[dev,llm,scoring]"
export ANTHROPIC_API_KEY="sk-..."
```

## 사용법

### 1. 카탈로그 탐색

```bash
finops-sim catalog list               # 전체 시나리오 목록
finops-sim catalog list --level L2    # L2 시나리오만
finops-sim catalog show L1-001        # 특정 시나리오 상세 정보
```

### 2. 문제 생성 (출제자용)

```bash
# 단일 시나리오 생성
finops-sim generate fixed --scenario-id L1-001 --output ./output

# 다른 시드로 변형 생성 (리소스 이름/메트릭이 달라짐)
finops-sim generate fixed --scenario-id L1-001 --seed 99 --output ./output

# L2 난이도 4문제 자동 선택 + 생성
finops-sim generate auto --level L2 --num-problems 4 --seed 42 --output ./output

# Claude API로 README 보강
finops-sim generate fixed --scenario-id L1-001 --use-llm --output ./output
```

### 3. 주차별 문제 생성 (스터디 운영용)

```bash
# config/weeks/week-04.yaml 설정 기반으로 전 멤버 문제 생성
python scripts/generate_week.py --week 4

# CLI 옵션으로 override
python scripts/generate_week.py --week 2 --level L2 --num-problems 4
```

주차 설정 파일(`config/weeks/week-NN.yaml`)에서 레벨, 문제 수, 활성 Generator, 채점 가중치를 제어합니다:

```yaml
# config/weeks/week-04.yaml
week: 4
level: "L2"
num_problems: 3
category: null
generators:
  - tf
  - metrics
  - cost_report
  - business_metrics        # L2부터 활성화
scoring_weights:
  schema: 1.0
  resource: 1.0
  savings: 1.0
  terraform: 1.0
  economics: 1.0            # L2부터 활성화
  alerts: 0.0
```

### 4. 학생 CLI (`finops-study`)

학생이 문제를 받고, 분석 결과를 검증/제출하는 CLI입니다.

```bash
# 내 문제 다운로드
finops-study pull --week 4

# AI 출력 검증 (spec/output_schema.json 기준)
finops-study validate ./my_output/analysis.json --level L2

# 제출
finops-study submit ./my_output/ --week 4 --scenario L2-014

# 채점 결과 확인
finops-study status --week 4

# Slack 알림 전송 (출력의 alerts[]를 Slack으로 발송)
finops-study submit ./my_output/ --week 4 --scenario L2-014 --notify-slack
```

**필요한 환경 변수:**
```bash
export GITHUB_USERNAME="your-username"
export GITHUB_TOKEN="ghp_..."
export FINOPS_REPO_OWNER="org-name"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."  # 선택
```

### 5. 채점

```bash
# 주차별 자동 채점 (정답 공개 후)
python scripts/score_submissions.py --week 4
```

두 가지 제출 형식을 지원합니다:

| 형식 | 감지 기준 | 채점 방식 |
|------|-----------|----------|
| **v2 구조화** | `analysis` 키 존재 | 6차원 composite scorer (Schema + Resource + Terraform + Savings + Economics + Alerts) |
| **v1 레거시** | `problem_identification` 키 존재 | 키워드 매칭 (하위 호환) |

## AI 출력 스펙

학생 AI는 `spec/output_schema.json`에 정의된 JSON Schema를 따라야 합니다.

### 레벨별 필수 필드

| 필드 | L1 | L2 | L3 |
|------|:---:|:---:|:---:|
| `analysis.problems_found[]` | ✅ | ✅ | ✅ |
| `analysis.unit_economics` | — | ✅ | ✅ |
| `analysis.elasticity` | — | — | ✅ |
| `recommendations[]` | ✅ | ✅ | ✅ |
| `alerts[]` | — | — | ✅ |
| `summary` | ✅ | ✅ | ✅ |
| `optimized_terraform` | 선택 | 선택 | 선택 |

### 출력 예시 (L1)

```json
{
  "analysis": {
    "problems_found": [
      {
        "resource": "volume-x1y2z3",
        "issue_type": "unused",
        "severity": "medium",
        "evidence": ["EBS I/O: 0 (전체 기간)", "gp2 500GB — 월 $50"],
        "recommendation": "스냅샷 생성 후 볼륨 삭제",
        "estimated_savings": 50
      }
    ]
  },
  "recommendations": [
    {
      "action": "snapshot_and_delete",
      "target": "volume-x1y2z3",
      "detail": "스냅샷 백업 후 삭제",
      "priority": "high",
      "estimated_savings": 50,
      "risk": "low"
    }
  ],
  "summary": {
    "total_issues_found": 1,
    "total_monthly_savings_usd": 50,
    "confidence_score": 85
  }
}
```

전체 예시는 `spec/examples/` 디렉토리를 참조하세요.

## 채점 상세

### 6차원 채점 모델

| 채점 항목 | 배점 | 설명 | 활성 레벨 |
|-----------|------|------|----------|
| **Schema** | 10 | JSON Schema 유효성 (에러당 -2점) | L1+ |
| **Resource** | 30 | 문제 리소스 식별 Precision(15) + Recall(15) | L1+ |
| **Terraform** | 15 | HCL 구조 유효성(5) + 문제 리소스 수정(5) + 인프라 보존(5) | L1+ |
| **Savings** | 20 | 절감액 추정 정확도 (±30% 만점, ±60% 반점) | L1+ |
| **Economics** | 15 | 단위경제 필드 완성도(5) + 계산 정확도(5) + 트렌드 방향(5) | L2+ |
| **Alerts** | 10 | 알림 존재(4) + 필드 구조(3) + severity 적절성(3) | L3 |

### 레벨별 활성 항목

| 레벨 | 활성 배점 합계 | 정규화 |
|------|--------------|--------|
| L1 | 75점 (Schema+Resource+TF+Savings) | → 100점 환산 |
| L2 | 90점 (+ Economics) | → 100점 환산 |
| L3 | 100점 (전부) | 그대로 |

## 데이터 생성 파이프라인

```
CLI 입력 (시나리오 ID or 레벨+개수)
    │
    ▼
카탈로그에서 시나리오 YAML 로드 + Pydantic 검증
    │
    ▼
가상 회사 프로필 생성 (업종, 규모, 성장 단계)
    │
    ▼
GenerationContext 조립 (시나리오 + 시드 + 회사정보)
    │
    ├──▶ TerraformGenerator      ──▶ main.tf                    (항상)
    │         │
    │         ▼ (ResourceManifest 공유)
    ├──▶ MetricsGenerator        ──▶ metrics/metrics.json        (항상)
    ├──▶ CostReportGenerator     ──▶ cost_report.json            (항상)
    │
    │  ── 레벨/카테고리 기반 조건부 활성화 ──
    │
    ├──▶ BusinessMetricsGenerator ──▶ business_metrics.json       (L2+)
    ├──▶ TagsInventoryGenerator   ──▶ tags_inventory.json         (L2+)
    ├──▶ CloudWatchFormatGenerator──▶ metrics/cloudwatch_format.json (L3)
    ├──▶ CURReportGenerator       ──▶ cur_report.csv              (L3)
    ├──▶ RISPCoverageGenerator    ──▶ ri_sp_coverage.json         (L3, rate 카테고리)
    │
    ├──▶ AnswerGenerator         ──▶ answer.json + scoring_rubric.json
    ├──▶ ReadmeGenerator         ──▶ README.md
    └──▶ LLM (optional)         ──▶ README 보강 + hint.txt
```

### Generator 활성화 규칙

| Generator | 시드 오프셋 | 활성화 조건 |
|-----------|-----------|------------|
| TerraformGenerator | base seed | 항상 |
| MetricsGenerator | base seed | 항상 |
| CostReportGenerator | +2000 | 항상 |
| BusinessMetricsGenerator | +3000 | L2, L3 |
| TagsInventoryGenerator | +4000 | L2, L3 |
| CloudWatchFormatGenerator | — (adapter) | L3 |
| CURReportGenerator | +6000 | L3 |
| RISPCoverageGenerator | +7000 | `rate` 카테고리 또는 `ri-sp` 태그 |

> **시드 안전성**: 새 Generator는 기존 Generator와 다른 시드 오프셋을 사용하므로, 기존 출력은 바이트 단위로 동일하게 유지됩니다.

### Generator별 출력 상세

**BusinessMetricsGenerator** (`business_metrics.json`)
- 30일 daily_metrics: `date`, `requests`, `orders`, `data_processed_gb`
- 트래픽 패턴을 시나리오 metrics_profile과 연동 (spike 시나리오면 트래픽도 스파이크)
- `current_unit_economics`: cost_per_order, cost_per_1k_requests, cost_to_revenue_pct

**TagsInventoryGenerator** (`tags_inventory.json`)
- 리소스별 5개 표준 태그(Service, Team, Env, CostCenter, Owner) 감사
- 문제 리소스: 20-40% 태그 준수 (나머지 누락)
- 디코이 리소스: 100% 태그 준수
- `tag_coverage_pct`, `missing_tags` 집계

**CloudWatchFormatGenerator** (`metrics/cloudwatch_format.json`)
- 기존 MetricsGenerator 출력을 AWS `GetMetricData` 응답 형식으로 변환
- `MetricDataResults[]`, ISO 8601 타임스탬프, `Values`, `StatusCode`

**CURReportGenerator** (`cur_report.csv`)
- AWS CUR 표준 15개 컬럼: `identity/LineItemId`, `lineItem/UsageStartDate`, `lineItem/ProductCode`, `lineItem/UnblendedCost`, `resourceTags/user:Service` 등
- 30일 × 리소스 수 행의 일별 라인 아이템

**RISPCoverageGenerator** (`ri_sp_coverage.json`)
- 기존 예약 목록(type, term, utilization)
- On-Demand 비율 및 월 지출
- 1년/3년 RI, 1년 SP 전환 시 예상 절감액

## 10주 커리큘럼

| 주차 | 레벨 | 주제 | 추가 입력 데이터 | 추가 채점 |
|------|------|------|---------------|----------|
| 1-3 | L1 | 낭비 리소스 식별 | — | Schema, Resource, Savings, TF |
| 4-5 | L2 | 단위경제 분석 | business_metrics | + Economics |
| 6-7 | L2 | 탄력성 진단 + 태그 거버넌스 | + tags_inventory | TF 가중 |
| 8 | L3 | RI/SP 최적화 | + ri_sp_coverage, cur_report | 전 항목 |
| 9 | L3 | 이상탐지 + 알림 생성 | + cloudwatch_format | + Alerts |
| 10 | L3 | 통합 실전 테스트 | 전부 (8개 파일) | 전 항목 |

상세 커리큘럼은 `docs/curriculum.md`를 참조하세요.

## 프로젝트 구조

```
src/
├── finops_sim/                         # 출제 엔진 (메인 패키지)
│   ├── cli.py                          # CLI 진입점 (click)
│   ├── config.py                       # 경로 상수, 생성 기본값
│   │
│   ├── catalog/                        # 시나리오 카탈로그
│   │   ├── loader.py                   # YAML 로드 + Pydantic 검증
│   │   ├── selector.py                 # 자동 모드 시나리오 선택
│   │   └── scenarios/                  # 40개 시나리오 (7 YAML 파일)
│   │       ├── L1_compute.yaml         #   L1 컴퓨트 10개
│   │       ├── L1_storage.yaml         #   L1 스토리지 3개
│   │       ├── L2_compute.yaml         #   L2 컴퓨트 패턴 7개
│   │       ├── L2_data_pipeline.yaml   #   L2 데이터 파이프라인 4개
│   │       ├── L3_network.yaml         #   L3 네트워크 6개
│   │       ├── L3_multi_account.yaml   #   L3 멀티계정/태깅 4개
│   │       └── L3_data_arch.yaml       #   L3 데이터 아키텍처 6개
│   │
│   ├── company/                        # 가상 회사 프로필
│   │   ├── profile.py                  # CompanyProfile 생성기
│   │   └── templates.yaml              # 8업종 × 4성장단계 템플릿
│   │
│   ├── generators/                     # 산출물 생성기
│   │   ├── base.py                     # 핵심 데이터클래스 (ScenarioDefinition 등)
│   │   ├── orchestrator.py             # 전체 파이프라인 조율
│   │   ├── terraform.py                # main.tf 생성 (Jinja2 + HCL)
│   │   ├── metrics.py                  # 30일 시계열 메트릭 JSON
│   │   ├── cost_report.py              # 6개월 비용 히스토리 JSON
│   │   ├── business_metrics.py         # 비즈니스 메트릭 + 단위경제 (L2+)
│   │   ├── tags_inventory.py           # 태그 감사 인벤토리 (L2+)
│   │   ├── cloudwatch_format.py        # AWS GetMetricData 형식 변환 (L3)
│   │   ├── cur_report.py               # AWS CUR CSV (L3)
│   │   ├── ri_sp_coverage.py           # RI/SP 커버리지 분석 (L3)
│   │   ├── answer.py                   # 정답 + 채점 기준 JSON
│   │   └── readme_gen.py               # 회사 배경 README.md
│   │
│   ├── scoring/                        # 다차원 자동 채점
│   │   ├── composite.py                # 채점 오케스트레이터 (레벨별 가중치)
│   │   ├── schema_scorer.py            # JSON Schema 유효성 (10점)
│   │   ├── resource_scorer.py          # 리소스 식별 Precision+Recall (30점)
│   │   ├── terraform_scorer.py         # HCL 유효성 + 수정 품질 (15점)
│   │   ├── savings_scorer.py           # 절감액 추정 정확도 (20점)
│   │   ├── economics_scorer.py         # 단위경제 계산 정확도 (15점, L2+)
│   │   └── alert_scorer.py             # 알림 생성 품질 (10점, L3)
│   │
│   ├── aws/                            # AWS 리소스 정보
│   │   ├── pricing.py                  # 근사 요금 모델
│   │   └── hcl_templates/              # Jinja2 HCL 템플릿 5개
│   │
│   ├── llm/                            # LLM 통합 (선택)
│   │   ├── interface.py                # LLMInterface Protocol
│   │   ├── claude.py                   # Claude API 구현
│   │   └── passthrough.py              # LLM 없이 템플릿 폴백
│   │
│   └── utils/
│       ├── random_helpers.py           # 시드 기반 시계열 생성 (11개 패턴)
│       └── validators.py               # 산출물 구조 검증
│
├── finops_study/                       # 학생용 CLI 패키지
│   ├── cli.py                          # finops-study 명령어 (pull/validate/submit/status)
│   ├── config.py                       # GitHub/Slack 환경변수
│   ├── validator.py                    # output_schema.json 검증
│   ├── github_client.py                # GitHub Contents API 래퍼
│   └── slack.py                        # Slack Block Kit 알림 전송
│
spec/                                   # AI 입출력 표준 스펙
├── output_schema.json                  # JSON Schema (draft-07)
├── input_spec.md                       # 입력 파일 형식 문서
└── examples/                           # 레벨별 출력 예시
    ├── L1_output.json
    ├── L2_output.json
    └── L3_output.json

config/
├── members.yaml                        # 스터디 멤버 목록
├── slack.yaml                          # Slack 연동 설정
└── weeks/                              # 주차별 설정
    ├── week-01.yaml ~ week-10.yaml     # 레벨, 문제수, generators, scoring_weights

scripts/
├── generate_week.py                    # 주차별 전 멤버 문제 생성
├── score_submissions.py                # 자동 채점 (v1 legacy + v2 composite)
├── reveal_answers.py                   # 정답 공개
└── parse_submission.py                 # 제출물 파싱

docs/
└── curriculum.md                       # 10주 커리큘럼 상세

tests/                                  # 91개 테스트
├── test_spec.py                        # 스펙 예시 검증 (7)
├── test_catalog.py                     # 카탈로그 검증 (20)
├── test_company.py                     # 회사 프로필 (4)
├── test_llm.py                         # LLM 통합 (6)
├── test_generators/
│   ├── test_e2e.py                     # E2E 생성 (12)
│   ├── test_integration.py             # 통합 테스트 (5)
│   ├── test_auto.py                    # 자동 생성 (5)
│   ├── test_business_metrics.py        # 비즈니스 메트릭 (5)
│   ├── test_tags_inventory.py          # 태그 인벤토리 (4)
│   ├── test_cloudwatch_format.py       # CloudWatch 형식 (5)
│   └── test_cur_report.py             # CUR 리포트 (5)
└── test_scoring/
    └── test_composite.py               # 채점 E2E (7)
```

## 핵심 설계

### 시드 기반 재현성
동일 시드 → 동일 출력. 리소스 이름, 메트릭 데이터, 비용 리포트 모두 시드로 결정됩니다.
시드를 바꾸면 같은 시나리오라도 다른 이름/수치로 생성되어 반복 학습에 활용 가능합니다.

각 Generator는 격리된 시드 오프셋(+2000, +3000, ...)을 사용하여 서로의 RNG 상태를 건드리지 않습니다.

### Problem + Decoy 구조
각 시나리오는 **문제 리소스**(비용 낭비)와 **디코이 리소스**(정상)를 함께 생성합니다.
AI가 단순히 "모든 것이 문제"라고 답하지 않도록 노이즈를 제공합니다.

태그 인벤토리에서도 이 구조를 유지합니다: 문제 리소스는 20-40% 태그 누락, 디코이는 100% 준수.

### 메트릭 시계열 패턴
11가지 패턴으로 현실적인 CloudWatch 메트릭을 생성합니다:
`zero`, `constant`, `normal`, `spike`, `sawtooth`, `step_down`, `step`, `normal_with_spike`, `spike_cycle`, `decreasing_linear`, `varying_constant`

### 점진적 난이도 확장
주차가 진행될수록 데이터 소스와 채점 차원이 점진적으로 추가됩니다:
- Week 1-3: 기본 3개 파일 → 4차원 채점
- Week 4-7: +비즈니스 메트릭, 태그 → 5차원 채점
- Week 8-10: +CUR, RI/SP, CloudWatch → 6차원 채점

### LLM 선택적 통합
`--use-llm` 없이도 완전히 동작합니다. LLM은 README를 더 자연스럽게 다듬는 용도로만 사용됩니다.

### 하위 호환
v1 제출 형식(`problem_identification` 키)과 v2 구조화 형식(`analysis` 키)을 모두 지원합니다.
채점 스크립트가 자동으로 감지하여 적합한 채점 방식을 적용합니다.

## 테스트

```bash
# 전체 테스트 (91개)
pytest -v

# Phase별 테스트
pytest tests/test_spec.py -v                         # 스펙 검증
pytest tests/test_generators/test_business_metrics.py -v  # 비즈니스 메트릭
pytest tests/test_generators/test_tags_inventory.py -v    # 태그 인벤토리
pytest tests/test_generators/test_cloudwatch_format.py -v # CloudWatch 형식
pytest tests/test_generators/test_cur_report.py -v        # CUR 리포트
pytest tests/test_scoring/test_composite.py -v            # 채점 E2E
pytest tests/test_generators/test_e2e.py -v               # 생성 E2E
```

## 생성 예시

```bash
$ finops-sim generate fixed --scenario-id L1-001 --output ./output

Generating scenario L1-001 (seed=42)...
Output: output/L1-001
Resources: 6 (4 problem, 2 decoy)
  main_tf: output/L1-001/main.tf
  metrics: output/L1-001/metrics/metrics.json
  cost_report: output/L1-001/cost_report.json
  answer: output/L1-001/answer.json
  scoring_rubric: output/L1-001/scoring_rubric.json
  readme: output/L1-001/README.md
  hint: output/L1-001/hint.txt

$ finops-sim validate output/L1-001
OK   L1-001

All 1 scenario(s) valid.
```

## 학생 워크플로우

```bash
# 1. 문제 받기
finops-study pull --week 4

# 2. AI 에이전트 개발 & 실행
python my_agent.py ./week-04/L2-014/

# 3. 출력 스펙 검증
finops-study validate ./output/analysis.json --level L2

# 4. 제출
finops-study submit ./output/ --week 4 --scenario L2-014

# 5. (선택) Slack 알림 전송
finops-study submit ./output/ --week 4 --scenario L2-014 --notify-slack

# 6. 결과 확인
finops-study status --week 4
```
