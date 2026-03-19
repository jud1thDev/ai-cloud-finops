# FinOps AI Study Platform

Cloud Club 9기 AI Cloud FinOps 스터디를 위한 **시뮬레이션 문제 자동 출제 + 웹 플랫폼**.

AWS 인프라의 비용 낭비 시나리오를 자동 생성하고, 웹에서 문제를 풀고 제출하면 자동 채점됩니다.

## 웹 플랫폼

| 페이지 | 기능 |
|--------|------|
| **Dashboard** | 주차별 문제 카드, 전체 통계 |
| **Problems** | 문제 뷰어 (Terraform, 메트릭 차트, 비용 리포트, 태그, CUR 등) |
| **Submit** | 답안 제출 (텍스트 분석 + Terraform 코드 + 파일 업로드) |
| **Scores** | 리더보드 + 개인 상세 점수 |
| **Profile** | 유저 정보, 제출 이력, 점수 트렌드, 멤버 전환 |
| **Materials** | 스터디 자료 게시판 (마크다운, PDF, 코드 업로드/프리뷰) |

- GitHub PAT 로그인 → 유저별 문제/제출/채점 분리
- 제출물은 GitHub repo에 직접 커밋 (GitHub = DB)

## 시나리오 카탈로그

총 **40개** 시나리오, 3단계 난이도.

### L1 — 명시적 문제 (13개)

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

## 10주 커리큘럼

| 주차 | 레벨 | 주제 | 입력 데이터 |
|------|------|------|------------|
| 1-3 | L1 | 낭비 리소스 식별 | Terraform + 메트릭 + 비용 리포트 |
| 4-5 | L2 | 단위경제 분석 | + 비즈니스 메트릭 |
| 6-7 | L2 | 탄력성 진단 + 태그 거버넌스 | + 태그 인벤토리 |
| 8 | L3 | RI/SP 최적화 | + CUR, RI/SP 커버리지 |
| 9 | L3 | 이상탐지 + 알림 생성 | + CloudWatch 형식 |
| 10 | L3 | 통합 실전 테스트 | 전체 (8개 파일) |

상세 커리큘럼은 [`docs/curriculum.md`](docs/curriculum.md)를 참조하세요.

## 문제에서 제공되는 데이터

| 파일 | 내용 | 레벨 |
|------|------|------|
| `main.tf` | AWS 인프라 Terraform 코드 (문제+정상 리소스 혼재) | 전체 |
| `metrics/metrics.json` | 30일 시간별 CloudWatch 메트릭 시계열 | 전체 |
| `cost_report.json` | 6개월 비용 히스토리 + 서비스별 breakdown | 전체 |
| `business_metrics.json` | 일별 트래픽 + 단위경제 지표 (cost/order 등) | L2+ |
| `tags_inventory.json` | 리소스별 태그 감사 (누락 태그, 커버리지) | L2+ |
| `metrics/cloudwatch_format.json` | AWS GetMetricData API 응답 형식 | L3 |
| `cur_report.csv` | AWS CUR 표준 CSV (일별 라인 아이템) | L3 |
| `ri_sp_coverage.json` | RI/SP 커버리지 + 절감 시뮬레이션 | L3 (rate) |

## 채점 (6차원)

| 항목 | 배점 | L1 | L2 | L3 |
|------|------|:---:|:---:|:---:|
| Schema 유효성 | 10 | O | O | O |
| Resource 식별 (Precision+Recall) | 30 | O | O | O |
| Terraform 수정 품질 | 15 | O | O | O |
| Savings 추정 정확도 | 20 | O | O | O |
| Unit Economics | 15 | - | O | O |
| Alerts 생성 | 10 | - | - | O |

활성 항목 합계를 100점으로 정규화합니다.

## 운영 가이드

### 멤버 등록

`config/members.yaml`에 GitHub username 추가:

```yaml
members:
  - username: github-username
    name: "이름"
    joined: "2026-03-19"
```

### 주차별 문제 생성

```bash
pip install -e ".[dev]"

# week config 기반 자동 생성
python scripts/generate_week.py --week 1

# 옵션 override
python scripts/generate_week.py --week 4 --level L2 --num-problems 3
```

주차 설정은 `config/weeks/week-NN.yaml`에서 관리합니다.

### 채점

```bash
python scripts/score_submissions.py --week 1
```

## 배포

1. GitHub repo Settings → Pages → Source: `main` branch, `/frontend` folder
2. `config/members.yaml`에 스터디원 등록
3. `config/group.yaml`에서 repo 경로 확인
4. GitHub Actions에 `GROUP_SALT` 시크릿 등록

## 프로젝트 구조

```
frontend/           # 웹 플랫폼 (GitHub Pages)
src/finops_sim/     # 출제 엔진 + 채점
src/finops_study/   # 학생 CLI
spec/               # AI 출력 스키마 + 예시
config/             # 멤버, 주차 설정
scripts/            # 문제 생성, 채점 스크립트
tests/              # 91개 테스트
docs/               # 커리큘럼
```
