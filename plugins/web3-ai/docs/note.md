2026-01-06

[1]
- info, retrieval = search (검색)
- RAG 의 한계, 검색이 잘 되는 지를 평가를 안 하고. 그냥 가지고 올라옴. 그냥 복붙. LLM 은 고정되어 있음. 엠베딩은 단순해서 할 수 있는 걸 함. similarity search 는 대충 비슷한 거 찾기 때문에 
- LLM 과 검색 (Prcesion / Recall) 의 분리가 필요함
    - Slack / Notion 검색 api 등.. (*) !!! ... Google Site tag => indexing 을 공부해야 함. obsidian tagging !!!?!
    - 검색 엔진이 벡터서치를 쓴 적이 없음.
- DB 검색엔진은, 모든 글자의 조합에 대해서 indexing 을 해서 O(1)의 시간복잡도로 검색을 할 수 있음. (+자동완성)
- 그 다음 aho colasic search (***)
- TF-IDF ... => 주식 embedding 이 필요가 없을 수도 있겠는데
*** entreprenuer 는 할 만한 가치가 있는 것을 찾아서 해야 함.

- 영어 에는 형태소에 어려움이 없음. flat 해서
- 한국어는 형태소 분석이 어려움. 10년 전만 해도 형태소 분석기가 없어서 검색엔진들이 고생함
=> embedding 으로 넘어감 (형태에서 의미로, breakthrough)
- llm 이전에 구글은 intent system 을 만들어냄 (knowledge graph)

[2]
LLM 리더보드랑, 검색이랑은 다른 거다. 
인덱싱, 엠베딩

embedding leaderboard - RTEB