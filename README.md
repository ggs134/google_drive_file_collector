# Google Drive 파일 수집기 (Recording Script Collector)

Google Drive에서 파일을 검색하고, Google 문서의 내용을 읽어서 CSV 파일로 저장하는 도구입니다.

## 주요 기능

### 1. Google Drive 파일 검색 (`drive_flie_list.py`)
- 날짜 범위로 파일 검색 (생성일/수정일 기준)
- 파일 타입 필터링 (PDF, DOCX, Google Docs, 이미지, 비디오 등)
- 파일명 키워드 검색
- 하위 폴더 재귀 검색
- Shared Drive 지원
- 결과를 Excel 또는 CSV로 저장

### 2. Google 문서 내용 읽기 (`google_drive_reader.py`)
- Google Docs를 텍스트로 읽기
- Google Sheets를 CSV로 읽기
- 단일 파일 또는 여러 파일 일괄 처리
- 파일 타입 자동 감지
- 읽은 결과를 CSV로 저장

### 3. 통합 워크플로우 (`test.py`)
- 파일 검색과 내용 읽기를 한 번에 처리
- 검색된 파일 ID를 자동으로 추출하여 내용 읽기

## 설치 방법

### 1. 필수 패키지 설치

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
pip install google-api-python-client
pip install pandas openpyxl
```

### 2. Google Cloud Console 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. **API 및 서비스 > 라이브러리**에서 **Google Drive API** 활성화
4. **API 및 서비스 > 사용자 인증 정보**에서 인증 정보 생성:
   - **OAuth 클라이언트 ID** 생성 (데스크톱 앱)
   - 또는 **서비스 계정** 생성
5. 생성된 `credentials.json` 파일을 프로젝트 루트 디렉토리에 저장

## 사용 방법

### 기본 사용 예제

#### 1. 파일 목록 검색하기

```python
from drive_flie_list import authenticate_google_drive, get_files_in_date_range
from googleapiclient.discovery import build

# 인증
creds = authenticate_google_drive()
service = build('drive', 'v3', credentials=creds)

# 특정 폴더에서 최근 7일간 생성된 Google Docs 검색
files = get_files_in_date_range(
    service,
    folder_id='your-folder-id',
    start_date='2025-11-10',
    end_date='2025-11-17',
    search_type='created',  # 'created' 또는 'modified'
    file_types=['gdoc'],  # Google Docs만
    filename_keywords=['gemini'],  # 파일명에 'gemini' 포함
    recursive=True,  # 하위 폴더 포함
    debug=True
)

# 파일 ID 추출
file_ids = [file['id'] for file in files]
```

#### 2. Google 문서 내용 읽기

```python
from google_drive_reader import GoogleDriveReader

# GoogleDriveReader 인스턴스 생성
reader = GoogleDriveReader(credentials_path='credentials.json')

# 단일 파일 읽기
file_name, content = reader.read_files('file-id-here')

# 여러 파일 읽기
results = reader.read_files([
    'file-id-1',
    'file-id-2',
    'file-id-3'
])

# 결과를 CSV로 저장
reader.save_results_to_csv(
    results, 
    output_file='results.csv', 
    include_content=True  # 전체 내용 포함
)
```

#### 3. 통합 워크플로우 (검색 + 읽기)

```python
from drive_flie_list import authenticate_google_drive, get_files_in_date_range
from googleapiclient.discovery import build
from google_drive_reader import GoogleDriveReader

# 1. 인증
creds = authenticate_google_drive()
service = build('drive', 'v3', credentials=creds)

# 2. 파일 검색
files = get_files_in_date_range(
    service,
    folder_id='your-folder-id',
    start_date='2025-11-10',
    end_date='2025-11-17',
    search_type='created',
    file_types=['gdoc'],
    recursive=True
)

# 3. 파일 ID 추출
file_ids = [file['id'] for file in files]

# 4. 파일 내용 읽기
reader = GoogleDriveReader()
results = reader.read_files(file_ids)

# 5. CSV로 저장
reader.save_results_to_csv(
    results, 
    output_file='results_full.csv', 
    include_content=True
)
```

## 주요 클래스 및 함수

### `GoogleDriveReader`

Google Drive 문서를 읽기 위한 클래스입니다.

#### 주요 메서드

- `read_file_content(file_id)`: 파일 타입을 자동 감지하여 내용 읽기
- `read_google_doc(file_id)`: Google Docs를 텍스트로 읽기
- `read_google_sheet(file_id)`: Google Sheets를 CSV로 읽기
- `read_files(file_ids)`: 단일 또는 여러 파일 읽기
- `save_results_to_csv(results, output_file, include_content)`: 결과를 CSV로 저장
- `save_to_separate_csv(results, output_dir)`: 각 파일을 개별 CSV로 저장

### `get_files_in_date_range()`

날짜 범위로 파일을 검색하는 함수입니다.

#### 주요 매개변수

- `service`: Google Drive API 서비스 객체
- `folder_id`: 검색할 폴더 ID (None이면 전체 드라이브)
- `start_date`: 시작 날짜 (datetime 또는 'YYYY-MM-DD' 형식)
- `end_date`: 종료 날짜 (datetime 또는 'YYYY-MM-DD' 형식)
- `search_type`: 'created' 또는 'modified'
- `recursive`: 하위 폴더 포함 여부
- `file_types`: 파일 타입 필터 (예: ['gdoc', 'pdf', 'image'])
- `filename_keywords`: 파일명에 포함될 키워드 리스트
- `exclude_keywords`: 제외할 키워드 리스트
- `debug`: 디버그 정보 출력 여부

## 지원하는 파일 타입

### 문서
- `pdf`, `doc`, `docx`, `txt`, `rtf`
- `gdoc` (Google Docs), `gsheet` (Google Sheets), `gslide` (Google Slides)

### 스프레드시트
- `xls`, `xlsx`, `csv`

### 이미지
- `image` (모든 이미지), `jpg`, `jpeg`, `png`, `gif`, `bmp`, `svg`, `webp`

### 비디오/오디오
- `video` (모든 비디오), `mp4`, `avi`, `mov`, `wmv`
- `audio` (모든 오디오), `mp3`, `wav`

### 기타
- `zip`, `rar`, `json`, `xml`, `html`, `css`, `js`, `py`

## 인증 방식

### OAuth 클라이언트 (기본)
- `credentials.json` 파일이 OAuth 클라이언트 형식인 경우
- 첫 실행 시 브라우저에서 인증 필요
- 인증 토큰은 `token.json` 또는 `token.pickle`에 저장

### 서비스 계정
- `credentials.json` 파일이 서비스 계정 형식인 경우
- 자동으로 인증 처리
- Shared Drive 접근 시 서비스 계정에 권한 부여 필요

## 출력 형식

### CSV 저장 옵션

#### 전체 내용 포함 (`include_content=True`)
```csv
순번,파일명,상태,내용_길이,내용
1,파일명1,성공,1234,전체 내용...
2,파일명2,성공,5678,전체 내용...
```

#### 요약 정보만 (`include_content=False`)
```csv
순번,파일명,상태,내용_길이,미리보기
1,파일명1,성공,1234,내용의 처음 200자...
2,파일명2,성공,5678,내용의 처음 200자...
```

## 예제 스크립트

### `csv_example.py`
CSV 저장 기능의 다양한 사용 예제를 포함합니다:
- 여러 파일을 하나의 CSV로 저장
- 요약 정보만 CSV로 저장
- 각 파일을 개별 CSV로 저장
- pandas를 사용한 고급 처리

### `example.py`
실제 사용 예제로, 파일 검색과 내용 읽기를 통합한 워크플로우를 보여줍니다.

## 주의사항

1. **권한**: Google Drive API 사용을 위해 적절한 권한이 필요합니다.
2. **Shared Drive**: Shared Drive의 파일에 접근하려면 `supportsAllDrives=True` 옵션이 필요하며, 서비스 계정에 권한이 부여되어 있어야 합니다.
3. **API 할당량**: Google Drive API는 일일 사용량 제한이 있습니다. 대량의 파일을 처리할 때는 주의하세요.
4. **인증 토큰**: `token.json` 또는 `token.pickle` 파일은 보안상 중요하므로 버전 관리에 포함하지 마세요.

## 문제 해결

### 인증 오류
- `credentials.json` 파일이 올바른 위치에 있는지 확인
- Google Cloud Console에서 API가 활성화되어 있는지 확인
- OAuth 클라이언트의 리디렉션 URI가 올바른지 확인

### 파일 접근 오류
- 파일 ID가 올바른지 확인
- 해당 파일에 대한 접근 권한이 있는지 확인
- Shared Drive의 경우 서비스 계정에 권한이 부여되어 있는지 확인

### 검색 결과가 없는 경우
- 날짜 범위가 올바른지 확인
- 폴더 ID가 올바른지 확인
- 파일 타입 필터가 너무 제한적인지 확인
- `recursive=True`로 설정하여 하위 폴더도 검색

## 라이선스

이 프로젝트는 개인 사용 목적으로 제작되었습니다.

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.

