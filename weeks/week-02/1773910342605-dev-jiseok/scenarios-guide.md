# FinOps 비용 낭비 시나리오 40선

---

## 🟢 L1 — 명시적 (Cost Explorer / Trusted Advisor에서 바로 보임)

청구서나 콘솔에서 직접 식별 가능. FinOps 입문자 레벨.

### 컴퓨트

| # | 시나리오 | 설명 |
|---|---------|------|
| 1 | **중지된 EC2 미삭제** | 인스턴스는 stop했는데 EBS는 계속 과금. "중지 = 무료"라는 흔한 착각. |
| 2 | **gp2 EBS 볼륨 미전환** | gp3 대비 20% 비싸고 성능도 낮음. 다운타임 없이 전환 가능한데 방치. |
| 3 | **비연결 Elastic IP** | 인스턴스에 붙어있지 않은 EIP는 시간당 $0.005. 쌓이면 무시 못할 금액. |
| 4 | **개발 환경 RDS Multi-AZ** | Dev/Staging DB에 고가용성 설정. 비용 2배인데 dev에서 HA 필요없음. |
| 5 | **사용 안 하는 Load Balancer** | 트래픽 0인데 ALB/NLB가 시간당 과금 중. 마이그레이션 후 미삭제. |
| 6 | **CloudWatch Logs retention = never** | 모든 Log Group이 영구 보존. 90일 이후 거의 안 보는 로그가 Standard 요금 무한 누적. |
| 7 | **오래된 EBS 스냅샷 방치** | 소스 볼륨 삭제 후에도 스냅샷 수백 개 잔존. GB당 $0.05/월. |
| 8 | **미사용 AMI + 연결 스냅샷** | AMI 등록 해제 안 하면 연결된 스냅샷도 계속 과금. |
| 9 | **ECR 이미지 Lifecycle 정책 없음** | 도커 이미지 버전이 수백 개 쌓이며 GB 단위 스토리지 낭비. |
| 10 | **DynamoDB 프로비전드 용량 과잉** | Read/Write Capacity Unit을 피크 기준으로 고정. 실제 사용률 10%인 경우 흔함. On-Demand로 전환하면 저절로 해결. |

### 스토리지

| # | 시나리오 | 설명 |
|---|---------|------|
| 11 | **S3 Lifecycle 정책 없음** | 모든 객체가 Standard($0.023/GB)에 영구 적체. Glacier Instant Retrieval로 내리면 83% 절감. |
| 12 | **S3 버전 관리 + 이전 버전 정리 없음** | 버전 관리 활성화 후 이전 버전 삭제 정책 미설정. 실제 사용 데이터의 3~10배 용량 누적. |
| 13 | **RDS 백업 보존 기간 35일** | 기본값 7일인데 누군가 35일로 설정. 자동 백업 스토리지 5배 과금. |

---

## 🟡 L2 — 패턴형 (메트릭 시계열 분석 필요)

청구서만 봐서는 안 보임. CloudWatch 메트릭이나 CUR을 일정 기간 뜯어봐야 발견.

### 컴퓨트 패턴

| # | 시나리오 | 설명 |
|---|---------|------|
| 14 | **Lambda 메모리 과잉 할당** | 3008MB 고정인데 실사용 180MB. Duration × Memory가 과금 기준이라 6배 낭비. AWS Lambda Power Tuning 툴로 최적 지점 찾을 수 있음. |
| 15 | **Lambda 타임아웃 과잉 설정** | 900초 설정인데 평균 실행 2초. 에러 시 900초 × 호출 수 과금. 실패 감지 못하면 청구서에서 안 보임. |
| 16 | **ECS Fargate vCPU/메모리 고정 과잉** | Fargate는 vCPU-시간 × 메모리-시간 단순 곱셈 요금이라, 1 vCPU → 0.5 vCPU로 줄이면 그 태스크 비용이 정확히 절반. P99 CPU 사용률이 20% 미만이면 즉시 후보. |
| 17 | **Auto Scaling warm-up 미설정** | 스케일아웃 이벤트 때 warm-up 없이 즉시 트래픽 유입 → 과부하 판단 → 또 스케일아웃 → 과잉 인스턴스 수 분간 유지. 짧은 시간에 반복 발생. |
| 18 | **Kinesis Shard 정적 과잉 프로비전** | 100 shard 운영 중 실제 사용 10. On-Demand 모드 전환이나 Application Auto Scaling 미적용. Shard 단가가 시간당 과금이라 CloudWatch IncomingBytes 메트릭 추세 분석해야 파악 가능. |
| 19 | **ElastiCache 노드 과잉** | Redis 클러스터 6노드인데 Hit Rate 98%, 연결 수 50개. 실제로는 2노드로 충분. CloudWatch의 CacheHits/Misses, CurrConnections 장기 추세 봐야 확인됨. |
| 20 | **RDS Read Replica 미사용** | Read Replica 3개 생성했는데 실제 읽기 트래픽이 Primary로만 향함. 애플리케이션 연결 설정 오류. 복제 지연 메트릭은 정상이라 Replica가 쓸모없다는 게 청구서에서 안 보임. |

### 데이터 파이프라인 패턴

| # | 시나리오 | 설명 |
|---|---------|------|
| 21 | **SQS Long Polling 미설정** | Short Polling으로 빈 큐를 초당 수십 회 폴링. API 호출 횟수 과금 + 빈 응답 낭비. CloudWatch의 NumberOfEmptyReceives 메트릭 보면 드러남. |
| 22 | **Kinesis Enhanced Fan-Out 불필요 활성화** | 표준 GetRecords 쓰면 무료인데 Enhanced Fan-Out($0.013/GB + $0.015/shard-hour)을 켜놓음. 실시간성 요구 없는 배치 처리에 적용. |
| 23 | **Athena 결과 S3 무제한 저장** | 쿼리 결과 버킷에 Lifecycle 없음. 수개월치 임시 쿼리 결과가 Standard 요금으로 쌓임. 보통 7일이면 충분. |
| 24 | **CloudWatch 커스텀 메트릭 1초 해상도** | High Resolution Metrics는 표준(60초)의 3배 요금. 운영 대시보드에 1초 해상도가 필요한 메트릭은 5% 미만인데 전체 적용. |

---

## 🔴 L3 — 아키텍처형 (멀티소스 로그 상관분석 + 설계 리뷰)

가장 돈 많이 새고, 가장 찾기 어려움. 단일 툴로는 거의 탐지 불가.

### 네트워크 설계 오류

| # | 시나리오 | 설명 |
|---|---------|------|
| 25 | **NAT Gateway Single-AZ 배치** | Private subnet이 3개 AZ에 걸쳐 있는데 NAT GW는 AZ-a 하나. AZ-b, AZ-c EC2가 AZ-a NAT 경유 시 cross-AZ $0.01/GB + NAT processing $0.045/GB 이중 과금. 이 패턴의 비용이 최적화 설계 대비 최대 79% 차이가 날 수 있음. AWS VPC Flow Logs를 AZ별로 집계해야 보임. |
| 26 | **Transit Gateway 불필요 경유** | Transit Gateway는 GB당 $0.02 데이터 처리 요금. 단순 VPC Peering으로 해결 가능한 통신을 TGW로 라우팅. 특히 같은 리전 내 VPC 간 트래픽이 TGW 경유하면 순수 낭비. |
| 27 | **PrivateLink Interface Endpoint 남발** | S3/DynamoDB는 Gateway Endpoint(무료)로 충분한데 Interface Endpoint($0.01/시간/AZ + GB 요금) 생성. AZ당 하나씩 만들면 3AZ × 여러 서비스 = 시간당 수십 달러. |
| 28 | **NLB Cross-Zone Load Balancing 활성화** | ALB는 cross-zone 무료지만 NLB는 GB당 $0.01. 고트래픽 서비스에서 NLB를 cross-zone으로 켜두면 월 수천 달러. 청구서 line item이 "DataTransfer-Regional-Bytes"로 뭉뚱그려져 원인 파악 어려움. |
| 29 | **S3 데이터를 NAT 경유 접근** | Private EC2 → NAT GW → Internet → S3. S3 Gateway Endpoint는 무료인데 설정 안 함. 데이터 집약 워크로드에서 NAT 비용이 EC2 비용 초과하는 경우도 있음. CUR의 usage type을 "NatGateway-Bytes"로 필터링해야 발견. |
| 30 | **VPN + Direct Connect 동시 유지** | 마이그레이션 과정에서 Direct Connect 개통 후에도 Site-to-Site VPN을 삭제 안 함. VPN connection-hour 과금 지속. 두 경로가 다 살아있어 청구서에서 이상하게 안 보임. |

### 멀티 계정 / 태깅 오류

| # | 시나리오 | 설명 |
|---|---------|------|
| 31 | **태그 없는 리소스 50%** | 태그 미적용 시 "unallocated spend" 블랙홀이 전체 예산의 50%를 잠식하는 경우도 있음. Cost Explorer에서 "No Tag" 비율이 높으면 최적화 기회가 어디에 있는지조차 모름. AWS Config Rule로 non-compliance 탐지 가능하지만 수정은 조직 차원 프로세스가 필요. |
| 32 | **Reserved Instance 패밀리 미스매치** | m5 RI를 구매했는데 시간이 지나며 워크로드가 c5, r5로 이동. RI가 적용되지 않고 on-demand 과금. Cost Explorer의 RI Utilization 리포트에서 80% 이하로 나오는데 왜 그런지 추적하려면 인스턴스 패밀리 변화 이력 분석 필요. |
| 33 | **Savings Plan Coverage Gap** | Compute SP를 구매했는데 커버리지 60%. 나머지 40%가 on-demand. 문제는 SP를 어떤 workload에 맞춰 샀는데 그 workload가 줄고 다른 곳이 늘었기 때문. Coverage 리포트는 보여주지만 원인 찾으려면 6개월치 사용 패턴 분석 필요. |
| 34 | **멀티 계정 미통합** | AWS Organizations 없이 계정 10개 운영. 계정마다 RI/SP 따로 구매. 통합 시 볼륨 할인 + SP/RI pooling으로 20~30% 추가 절감 가능. 하지만 현재 상태에서는 낭비가 어디서 나는지조차 파악 불가. |

### 데이터 아키텍처 오류

| # | 시나리오 | 설명 |
|---|---------|------|
| 35 | **Athena 파티셔닝 없는 대형 테이블** | 날짜/리전 파티션 없이 전체 스캔. 동일 쿼리가 파티션 있으면 100GB 스캔, 없으면 10TB 스캔. TB당 $5이니 100배 차이. 쿼리 결과는 같아서 개발자가 문제인 줄 모름. |
| 36 | **Redshift 클러스터 24/7 Always-On** | 배치 분석용인데 야간/주말에도 풀 가동. Redshift Serverless나 스케줄 일시정지 미적용. 실제 사용 시간이 운영 시간의 30%인데 100% 과금. |
| 37 | **S3 Cross-Region Replication 전체 적용** | DR 목적인데 prefix 필터 없이 전체 복제. 로그, 임시 파일, 캐시 데이터까지 전부 복제. 실제 DR에 필요한 데이터는 20%인데 100% 복제 비용 지불. CUR에서 DataTransfer-Out-Bytes 보면 크게 나오는데 왜 큰지 파악하려면 복제 규칙 설계 리뷰 필요. |
| 38 | **EKS Pod resource request 과잉** | request.cpu를 실제 사용의 5~10배로 설정. 노드에 Pod가 3~4개밖에 못 들어가 CPU 15% 쓰는 노드가 20개 운영 중. Karpenter/VPA 없으면 CloudWatch에서 CPU 낮다는 건 보이는데 "왜 노드가 이렇게 많냐"는 Pod request 설정 보기 전엔 모름. |
| 39 | **CloudFront 없이 S3 Direct Egress** | 글로벌 사용자에게 S3 us-east-1 직접 서빙. CloudFront 경유 시 $0.0085/GB인데 직접 egress는 $0.09/GB. 10배 차이. 게다가 지연시간도 높음. S3 Access Log 분석해서 지역별 접근 패턴 봐야 CloudFront 도입 ROI 계산 가능. |
| 40 | **RDS Proxy 없는 Lambda→RDS 직접 연결** | Lambda 수천 개 동시 실행 시 RDS 연결 수 폭발. RDS 인스턴스를 연결 수 때문에 r6g.4xlarge로 업사이징. 실제 쿼리 부하는 r6g.large로 충분. RDS Proxy 도입 시 인스턴스 다운사이징 가능한데, 원인이 "연결 수" 문제인지 "쿼리 부하" 문제인지는 RDS Performance Insights 봐야 구분 가능. |

---

## 📊 요약

| 레벨 | 패턴 수 | 탐지 방법 | 대표 툴 |
|------|--------|----------|--------|
| **L1** | 13개 | Cost Explorer, Trusted Advisor 직접 확인 | OptScale, CostMinimizer |
| **L2** | 11개 | CloudWatch 메트릭 시계열, CUR 필터링 | Compute Optimizer, S3 Storage Lens |
| **L3** | 16개 | VPC Flow Logs + CUR 상관분석, 아키텍처 리뷰 | 직접 Athena 쿼리, 설계 검토 |

> **L3가 가장 중요한 이유** — 어떤 FinOps 툴도 자동으로 다 잡지 못하기 때문입니다. 그래서 직접 설계하고 직접 찾는 훈련이 의미가 있습니다.
