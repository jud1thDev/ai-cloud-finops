# FinOps AI 스터디 10주 커리큘럼

## 개요

10주간 FinOps AI 에이전트를 점진적으로 구축하며 실무 FinOps 역량을 키우는 커리큘럼입니다.
매주 난이도와 데이터 소스가 확장되며, 최종적으로 실환경 수준의 통합 분석 에이전트를 완성합니다.

---

## 주차별 구성

### Week 1-3: L1 기초 — 낭비 리소스 식별

**목표**: Terraform + 메트릭 + 비용 데이터를 파싱하여 명시적 비용 낭비를 찾는 AI 구축

| 항목 | 내용 |
|------|------|
| 레벨 | L1 |
| 입력 데이터 | `main.tf`, `metrics/metrics.json`, `cost_report.json` |
| 필수 출력 | `analysis.problems_found`, `recommendations`, `summary` |
| 채점 기준 | Schema(10) + Resource(30) + Savings(20) + Terraform(15) |
| 주요 시나리오 | 중지된 EC2, 미사용 EBS, 유휴 RDS, 미연결 EIP |

**Week 1**: 첫 AI 에이전트 뼈대 구축, `main.tf` 파싱
**Week 2**: 메트릭 시계열 분석 추가, 비용 리포트 연동
**Week 3**: 종합 L1 시나리오 3개 풀기

---

### Week 4-5: L2 단위경제 분석

**목표**: 비즈니스 메트릭 기반 단위경제(Cost per Order, Cost per 1K Requests) 분석

| 항목 | 내용 |
|------|------|
| 레벨 | L2 |
| 추가 입력 | `business_metrics.json` |
| 추가 출력 | `analysis.unit_economics` |
| 채점 추가 | Economics(15) |
| 주요 시나리오 | 오버프로비저닝, 비용 효율성 악화, DynamoDB/RDS 과대 설정 |

**Week 4**: `business_metrics.json` 파싱, 단위경제 KPI 계산 로직 구현
**Week 5**: 오버프로비저닝 패턴 탐지 심화, 트렌드 분석

---

### Week 6-7: L2 탄력성 진단

**목표**: 태그 거버넌스 분석 + Terraform 수정안 생성

| 항목 | 내용 |
|------|------|
| 레벨 | L2 |
| 추가 입력 | `tags_inventory.json` |
| 채점 강화 | Terraform(15) 가중 |
| 주요 시나리오 | 태그 누락 리소스, 비용 할당 불가 리소스 |

**Week 6**: 태그 인벤토리 분석, 태그 누락 리소스 탐지
**Week 7**: Terraform HCL 수정안 자동 생성, 태그 일괄 적용

---

### Week 8: L3 RI/SP 최적화

**목표**: CUR 데이터 + RI/SP 커버리지 분석으로 요금제 최적화 전략 수립

| 항목 | 내용 |
|------|------|
| 레벨 | L3 |
| 추가 입력 | `cur_report.csv`, `ri_sp_coverage.json` |
| 추가 출력 | `analysis.elasticity`, `alerts` |
| 채점 | 전 항목 활성화 |
| 주요 시나리오 | On-Demand 과다 사용, RI 미활용, SP 전략 부재 |

---

### Week 9: L3 이상탐지 + 알림

**목표**: CloudWatch 형식 메트릭에서 이상 감지, Slack/Email 알림 생성

| 항목 | 내용 |
|------|------|
| 레벨 | L3 |
| 추가 입력 | `metrics/cloudwatch_format.json` |
| 채점 강화 | Alerts(10) |
| 주요 시나리오 | 비용 스파이크, 갑작스런 사용량 증가, 야간 유휴 비용 |

---

### Week 10: L3 통합 실전

**목표**: 모든 데이터 소스를 통합 분석하는 최종 AI 에이전트

| 항목 | 내용 |
|------|------|
| 레벨 | L3 |
| 입력 | 전체 (8개 파일) |
| 출력 | 전체 (problems, unit_economics, elasticity, alerts, terraform) |
| 채점 | 전 항목 (100점 만점) |

---

## 채점 배점 (레벨별)

| 채점 항목 | L1 | L2 | L3 |
|-----------|-----|-----|-----|
| Schema 유효성 | 10 | 10 | 10 |
| Resource 식별 | 30 | 30 | 30 |
| Terraform 수정 | 15 | 15 | 15 |
| Savings 추정 | 20 | 20 | 20 |
| Unit Economics | - | 15 | 15 |
| Alerts 생성 | - | - | 10 |
| **합계** | **75** | **90** | **100** |

> 점수는 활성 항목 대비 정규화하여 100점 만점으로 환산됩니다.

---

## 학생 워크플로우

```bash
# 1. 문제 받기
finops-study pull --week 4

# 2. AI 에이전트 개발 & 실행
python my_agent.py ./week-04/L2-001/

# 3. 출력 검증
finops-study validate ./output/analysis.json --level L2

# 4. 제출
finops-study submit ./output/ --week 4 --scenario L2-001

# 5. 결과 확인
finops-study status --week 4
```
