# Web3 AI Plugin

Web3/Ethereum 개발과 AI 에이전트 시스템 구축을 위한 전문 에이전트 모음입니다.

## Agents

### 1. humanities-web3-agent
**문사철(文史哲) 인문학 × Web3/AI 전문가**

블록체인과 AI를 인문학적 관점에서 분석하는 에이전트입니다.

#### 주요 영역
- **철학(哲)**: 탈중앙화 정치철학, 디지털 존재론, AI 윤리학, 화폐철학
- **역사(史)**: 화폐사, 기술혁명사, 사이퍼펑크 계보학, AI 발전사
- **문학(文)**: 사이버펑크 문학, 디지털 저자성, 크립토 내러티브 분석

#### 사용 예시
```
"스마트 컨트랙트와 사회계약론의 관계를 분석해줘"
"NFT의 존재론적 지위는 무엇인가?"
"비트코인을 화폐 역사의 맥락에서 설명해줘"
"사이버펑크 문학이 예언한 것과 현실 Web3를 비교해줘"
"AI 에이전트에게 도덕적 책임을 물을 수 있는가?"
```

---

### 2. x402-ethereum-agent
**Web3 및 Ethereum 블록체인 개발 전문가**

X402 프로토콜과 Ethereum 생태계 개발에 특화된 에이전트입니다.

#### 주요 기능
- X402 프로토콜 구현 및 통합
- Solidity 스마트 컨트랙트 개발 (ERC-20, ERC-721, ERC-1155, ERC-4337)
- Layer 2 솔루션: Polygon, Arbitrum, Optimism, Base, zkSync
- DeFi 프로토콜 통합: Uniswap, Aave, Compound
- Web3 프론트엔드: Wagmi, Viem, RainbowKit
- NFT 개발 및 마켓플레이스 구축
- Account Abstraction (ERC-4337)

#### 사용 예시
```
"X402 토큰 표준으로 거버넌스 시스템 구현해줘"
"ERC-4337 account abstraction으로 가스리스 트랜잭션 만들어줘"
"Uniswap V3 유동성 풀 통합해줘"
"NFT 마켓플레이스 스마트 컨트랙트 작성해줘"
```

---

### 3. ai-agent
**AI 에이전트 개발 전문가**

LLM 기반 에이전트, 멀티 에이전트 시스템, RAG 구현에 특화된 에이전트입니다.

#### 주요 기능
- LLM 통합: OpenAI, Anthropic, Google, 오픈소스 모델
- 에이전트 프레임워크: LangChain, LangGraph, CrewAI, AutoGPT
- RAG 시스템: Pinecone, Weaviate, ChromaDB
- A2A (Agent-to-Agent) 프로토콜 구현
- 멀티 에이전트 협업 시스템
- 에이전트 평가 및 모니터링

#### Context7 MCP 통합
라이브러리별 최신 문서를 자동으로 가져와 정확한 코드를 생성합니다.

#### 사용 예시
```
"LangChain으로 RAG 기반 고객 지원 에이전트 만들어줘"
"CrewAI로 멀티 에이전트 리서치 시스템 구축해줘"
"A2A 프로토콜로 에이전트 간 통신 구현해줘"
"LangGraph로 워크플로우 기반 에이전트 만들어줘"
```

---

### 4. agentic-commerce-analyst
**에이전트 상거래 및 결제 프로토콜 분석가**

Google AP2/A2A 프로토콜, 전통 결제 시스템, 리테일/이커머스 비즈니스 전략 분석에 특화된 에이전트입니다.

#### 주요 영역
- **결제 프로토콜**: Google AP2 (Mandates), A2A, A2A x402 Extension
- **전통 결제**: Visa, Mastercard, PayPal, Stripe, BNPL
- **비즈니스 분석**: 에이전틱 상거래 시장 트렌드, 경쟁 분석
- **규제/리스크**: 사기 방지, 소비자 보호, 컴플라이언스

#### 웹검색 규칙 (중요)
- 검색 전 현재 날짜 확인
- 검색 쿼리에 현재 연도 명시 (예: "AP2 protocol 2026")
- 오래된 정보 필터링

#### 사용 예시
```
"Google AP2 프로토콜 작동 방식 설명해줘"
"에이전트 상거래 시장 전망 분석해줘"
"A2A vs MCP vs AP2 비교해줘"
"전통 결제 시스템과 에이전트 결제의 차이점"
```

---

## 디렉토리 구조

```
plugins/web3-ai/
├── agents/
│   ├── ai-agent.md                    # AI 에이전트 개발 에이전트
│   ├── agentic-commerce-analyst.md    # 에이전트 상거래/결제 분석가
│   ├── humanities-web3-agent.md       # 문사철 인문학 × Web3/AI 에이전트
│   └── x402-ethereum-agent.md         # Web3/Ethereum 개발 에이전트
├── commands/                           # (예정) 슬래시 명령어
├── skills/                             # (예정) 재사용 가능한 지식
├── docs/                               # 레퍼런스 문서
└── local/                              # 개인 노트 (Gitignored)
```

## 사용 방법

1. 플러그인 설치 후 자동으로 에이전트 사용 가능
2. Web3 개발 질문 시 `x402-ethereum-agent` 자동 호출
3. AI 에이전트 개발 질문 시 `ai-agent` 자동 호출
4. 또는 명시적으로 에이전트 지정 가능

## 플러그인 변경 시 체크리스트

플러그인에 agents, commands, skills를 추가/삭제했다면 **반드시** 아래 파일도 업데이트하세요:

```
/.claude-plugin/marketplace.json
```

### marketplace.json 역할
- 모든 플러그인의 메타데이터와 구성요소를 중앙에서 관리
- Claude Code가 플러그인을 인식하고 로드하는 데 사용
- agents, commands, skills 경로가 여기에 등록되어야 실제로 동작

### 이 플러그인의 현재 등록 상태
```json
{
  "name": "web3-ai",
  "version": "1.1.0",
  "commands": [],
  "agents": [
    "./agents/ai-agent.md",
    "./agents/agentic-commerce-analyst.md",
    "./agents/humanities-web3-agent.md",
    "./agents/x402-ethereum-agent.md"
  ],
  "skills": []
}
```

### 변경 예시
새 에이전트 `my-new-agent.md` 추가 시:
1. `agents/my-new-agent.md` 파일 생성
2. `/.claude-plugin/marketplace.json`의 `web3-ai.agents` 배열에 추가

## 키워드

`web3` `ethereum` `x402` `blockchain` `smart-contracts` `defi` `nft` `ai` `agent` `llm` `langchain` `rag` `multi-agent` `a2a` `humanities` `philosophy` `history` `literature` `ethics` `digital-humanities` `agentic-commerce` `ap2-protocol` `agent-payments`

## License

MIT
