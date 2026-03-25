## Analysis

### Week
2

### Scenario ID
L1-001

### Problem Identification
- 사용되지 않는 EBS 볼륨: ebs-volume-ly10d7
- 사용되지 않는 EBS 볼륨: ebs-volume-g1rhjf
- 사용되지 않는 EBS 볼륨: ebs-volume-wcp38l
- 과대 프로비저닝 가능성이 있는 EC2: instance-cvi04q

### Root Cause
- 중지된 인스턴스에 연결되었거나 사실상 유휴 상태인 500GB gp2 EBS 볼륨 3개가 지속적으로 비용을 발생시키고 있습니다.
- 6개월 평균 낭비 비용은 $151.46이며, 동일한 낭비 패턴이 반복되고 있습니다.
- instance-cvi04q의 평균 CPU 사용률은 0.56%로 낮아 과대 프로비저닝 가능성이 있습니다.

### Proposed Solution
- 1. ebs-volume-ly10d7, ebs-volume-g1rhjf, ebs-volume-wcp38l 볼륨이 실제 운영에 필요한지 오너 확인
- 2. 필요 없으면 즉시 삭제, 보존 필요 시 스냅샷 생성 후 볼륨 삭제
- 3. 재발 방지를 위해 EBS 생성 시 owner, ttl, environment 태그를 강제
- 4. m5.xlarge 인스턴스는 성능 테스트 후 더 작은 인스턴스로 리사이징 검토

### Estimated Monthly Savings (USD)
260