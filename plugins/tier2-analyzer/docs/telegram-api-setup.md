# Telegram API 설정 가이드

SI+ 에이전트를 위한 텔레그램 API 설정 방법입니다.

## 1. API 키 발급

1. https://my.telegram.org 접속
2. 로그인 (전화번호 인증)
3. "API development tools" 클릭
4. App 정보 입력:
   - App title: Stock Analyzer SI+
   - Short name: siplus
   - Platform: Desktop
5. `api_id`와 `api_hash` 복사

## 2. Telethon 설치

```bash
pip install telethon
```

## 3. 환경변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
# .env 파일 편집하여 실제 값 입력
```

필요한 환경변수:

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `TELEGRAM_API_ID` | API ID (숫자) | `12345678` |
| `TELEGRAM_API_HASH` | API Hash (문자열) | `abc123def456...` |
| `TELEGRAM_PHONE` | 인증 전화번호 | `+821012345678` |

## 4. 첫 인증

```python
from telethon import TelegramClient

api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
phone = '+821012345678'

client = TelegramClient('session_siplus', api_id, api_hash)
client.start(phone=phone)
# SMS 인증 코드 입력 필요 (최초 1회)
```

## 5. 세션 파일

- 첫 인증 후 `session_siplus.session` 파일 생성
- 이후 인증 없이 재사용 가능
- **주의**: 세션 파일은 git에 포함하지 않음 (`.gitignore`에 추가됨)

## 6. 채널 접근

| 채널 유형 | 접근 방법 |
|----------|----------|
| 공개 채널 | 채널 username으로 접근 가능 |
| 비공개 채널 | 초대 링크로 가입 필요 |

### 제한사항

- 분당 메시지 수집 제한 있음 (FloodWait)
- FloodWait 발생 시 자동 대기 후 재시도

## 7. 문제 해결

### FloodWaitError

```python
from telethon.errors import FloodWaitError
import asyncio

try:
    messages = await client.get_messages(channel, limit=100)
except FloodWaitError as e:
    print(f"Rate limited. Waiting {e.seconds} seconds...")
    await asyncio.sleep(e.seconds)
```

### 채널을 찾을 수 없음

- 채널 username 확인 (@ 제외)
- 비공개 채널인 경우 먼저 가입 필요
- 채널이 삭제/비활성화된 경우
