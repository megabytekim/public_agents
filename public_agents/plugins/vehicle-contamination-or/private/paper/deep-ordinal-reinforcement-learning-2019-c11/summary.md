# Deep Ordinal Reinforcement Learning

## 기본 정보

| 항목 | 내용 |
|------|------|
| **논문** | Deep Ordinal Reinforcement Learning |
| **저자** | Alexander Zap, Tobias Joppen, Johannes Fürnkranz |
| **연도** | 2019 |
| **인용수** | 11 |
| **arXiv** | [1905.02005](https://arxiv.org/abs/1905.02005) |
| **카테고리** | Reinforcement Learning, Ordinal Rewards |
| **구현 난이도** | ⭐⭐⭐⭐☆ (4/5) |
| **세차 적용성** | ⭐☆☆☆☆ (1/5) |

---

## 핵심 원리

### 문제 인식
기존 강화학습은 **numerical rewards**를 사용하지만:
1. **Reward shaping 어려움**: 정확한 수치 설정 필요 (비직관적)
2. **Reward hacking**: 잘못된 보상 함수 악용 가능
3. **Infinite rewards 필요**: 치명적 행동 방지 위해 -∞ 같은 인위적 값 사용

### 해결책
**Ordinal Rewards**를 사용하는 강화학습:
- Rewards를 **순위(rank)**로만 표현: r1 ≺ r2 ≺ ... ≺ rn
- 크기는 무시, 순서만 중요
- Reward 설계 간소화: "좋음 > 나쁨" 같은 자연스러운 순서만 정의

### 수학적 표현

**Ordinal MDP**:
```
(S, A, T, R_o)
R_o: S × A × S → {1, ..., n}  (ordinal reward tiers)
```

**Distribution-based aggregation**:
```
D(s,a) = [d_1(s,a), ..., d_n(s,a)]  (frequency of each reward tier)
P(s,a) = normalize(D(s,a))  (probability distribution)
```

**Value function (Measure of Statistical Superiority)**:
```
V_π(s) = F(P(s,a))
F(P(s,a)) = E[P(a ≻ a')] = Σ P(a ≻ a') / (k-1)

P(a ≻ a') = Σ_o p_o(s,a) · p_{<o}(s,a') + 0.5 · p_o(s,a')
```
- `p_{<o}(s,a')`: a'가 rank o보다 낮은 확률
- Best-choice maximization (not sum maximization)

**Ordinal Q-learning update**:
```
D(s,a) ← D(s,a) + α · [e_i + γ·D(s', π*(s')) - D(s,a)]
```
- e_i: unit vector (받은 ordinal reward i)

**Ordinal DQN**:
- K개 neural network (action마다 1개)
- 각 network output: n-dim distribution D_a(s)
- Target: D̂_a(s) = e_ro + γ·D_π*(s')(s')

---

## 장점

1. **Reward shaping 간소화**: 순서만 정의하면 됨 (수치 불필요)
2. **Reward hacking 완화**: 순서만 바뀌면 exploit 어려움
3. **Domain-agnostic**: 의료, 게임, 로봇 등 어디든 적용 가능
4. **성능 comparable**: CartPole, Acrobot에서 numerical RL과 유사 성능

---

## 단점

1. **Computational overhead**:
   - Measure of statistical superiority 계산 비용 1.5~2배
   - K개 network 필요 (DQN의 경우)
2. **Metric 정보 손실**: reward 크기 차이 무시 → 정밀 제어 어려움
3. **Sample efficiency 낮음**: numerical RL보다 더 많은 episode 필요
4. **RL 전문 지식 필요**: Q-learning, DQN 이해 필수

---

## 코드 예시 (Ordinal Q-learning pseudo-code)

```python
import numpy as np

class OrdinalQLearning:
    def __init__(self, n_states, n_actions, n_tiers, alpha=0.1, gamma=0.9):
        # Distribution table: (states, actions, tiers)
        self.D = np.ones((n_states, n_actions, n_tiers)) / n_tiers
        self.n_tiers = n_tiers
        self.alpha = alpha
        self.gamma = gamma

    def measure_of_superiority(self, P_a, P_a_prime):
        """Calculate P(a > a')"""
        prob = 0
        for o in range(self.n_tiers):
            p_less = np.sum(P_a_prime[:o])  # a' gets tier < o
            prob += P_a[o] * (p_less + 0.5 * P_a_prime[o])
        return prob

    def select_action(self, state):
        """Select action with highest F(P(s,a))"""
        P = self.D[state] / self.D[state].sum(axis=1, keepdims=True)
        values = []
        for a in range(len(P)):
            # Average winning probability against all other actions
            win_probs = [self.measure_of_superiority(P[a], P[a_prime])
                         for a_prime in range(len(P)) if a_prime != a]
            values.append(np.mean(win_probs))
        return np.argmax(values)

    def update(self, state, action, ordinal_reward, next_state):
        """Q-learning style update for distributions"""
        # Unit vector for received ordinal reward
        e_i = np.zeros(self.n_tiers)
        e_i[ordinal_reward - 1] = 1

        # Optimal action in next state
        next_action = self.select_action(next_state)

        # Target distribution
        target = e_i + self.gamma * self.D[next_state, next_action]

        # Update distribution
        self.D[state, action] += self.alpha * (target - self.D[state, action])
```

---

## 세차 적용 아이디어

### 1. 로봇 팔 세차 제어 (이론적 가능성만)
**시나리오**: 세차 로봇이 부위별 오염도 관찰 → 행동(물뿌리기, 브러시 강도) 선택

**Ordinal RL 적용**:
```
States: (오염도 이미지, 로봇 위치, 물 사용량)
Actions: {약한 물살, 강한 물살, 브러시, 이동}
Ordinal Rewards:
  r1 (나쁨): 오염 그대로, 물 낭비
  r2 (보통): 오염 약간 감소
  r3 (좋음): 오염 많이 감소
  r4 (최고): 오염 완전 제거, 물 절약
```

**문제점**:
- 세차는 **deterministic task** → RL 필요 없음 (규칙 기반으로 충분)
- 실시간 학습 불가능 (시뮬레이션 환경 구축 비용 큼)
- Ordinal RL 장점(reward shaping 간소화)이 이 도메인에서 불필요

### 2. 세차 스케줄링 최적화 (매우 간접적)
**시나리오**: 세차장에서 여러 차량 대기 → 순서 및 세차 강도 결정

**Ordinal RL 적용**:
```
States: (대기 차량 수, 각 차량 오염도, 남은 시간)
Actions: {다음 차량 선택, 세차 강도 설정}
Ordinal Rewards:
  r1: 고객 불만족 (대기 시간 길음)
  r2: 평범한 서비스
  r3: 고객 만족
  r4: 최적 효율 + 고객 만족
```

**문제점**:
- 전통적 스케줄링 알고리즘(greedy, priority queue)이 더 효율적
- Ordinal RL의 sample inefficiency → 실시간 적용 불가

---

## 총평

**Deep Ordinal RL**은 강화학습의 흥미로운 변형이지만, **차량 오염도 분류와는 관련 없음**.

**핵심 차이**:
1. **RL vs Supervised Learning**: 차량 오염도는 supervised classification (RL 불필요)
2. **Sequential decision vs Single prediction**: RL은 시간에 따른 행동 선택, 오염도는 1회 예측
3. **Exploration vs Recognition**: RL은 환경 탐색, 오염도는 패턴 인식

**세차 도메인 적용성**: ⭐☆☆☆☆
- 로봇 제어나 스케줄링에 이론적 적용 가능하지만 비효율적
- 규칙 기반 시스템이 더 실용적

**추천도**: ❌ **구현 불필요** (차량 오염도 OR과 무관)

**혼동 주의**:
- "Ordinal" 키워드 때문에 검색되었지만, 이 논문은 **RL reward 표현 방식**에 관한 것
- 우리가 필요한 것은 **Ordinal Classification/Regression** (CORAL, CORN 등)
