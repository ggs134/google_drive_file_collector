"""
Google Shared Drive 문서 조회 스크립트

이 스크립트는 Google Drive API를 사용하여 Shared Drive에 있는 
Google 문서의 내용을 파일 ID로 조회합니다.
"""

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
from googleapiclient.http import MediaIoBaseDownload


class GoogleDriveReader:
    """Google Drive 문서를 읽기 위한 클래스"""
    
    def __init__(self, credentials_path='credentials.json'):
        """
        초기화 메서드
        
        Args:
            credentials_path (str): credentials JSON 파일 경로 (기본값: 현재 디렉토리의 credentials.json)
                                   서비스 계정 또는 OAuth 클라이언트 형식 모두 지원
        """
        self.credentials_path = credentials_path
        self.service = self._build_service()
    
    def _build_service(self):
        """Google Drive API 서비스 생성"""
        import json
        import os
        
        try:
            # credentials 파일 읽기
            with open(self.credentials_path, 'r') as f:
                creds_data = json.load(f)
            
            # 서비스 계정인지 OAuth 클라이언트인지 자동 감지
            if 'type' in creds_data and creds_data['type'] == 'service_account':
                # 서비스 계정 인증
                print("서비스 계정 인증 사용")
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            else:
                # OAuth 클라이언트 인증
                print("OAuth 클라이언트 감지됨")
                print("\nOAuth 클라이언트를 사용하려면 먼저 인증이 필요합니다.")
                print("다음 단계를 진행하세요:")
                print("1. Google Cloud Console에서 서비스 계정을 생성하거나")
                print("2. OAuth 인증 플로우를 완료해야 합니다.\n")
                
                # OAuth 인증 플로우 시도
                from google_auth_oauthlib.flow import InstalledAppFlow
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                
                # token.json 파일이 있는지 확인
                token_path = 'token.json'
                if os.path.exists(token_path):
                    credentials = Credentials.from_authorized_user_file(
                        token_path,
                        scopes=['https://www.googleapis.com/auth/drive.readonly']
                    )
                else:
                    # 브라우저를 통한 인증
                    credentials = flow.run_local_server(port=0)
                    
                    # token 저장
                    with open(token_path, 'w') as token:
                        token.write(credentials.to_json())
                    print(f"인증 토큰이 {token_path}에 저장되었습니다.")
            
            service = build('drive', 'v3', credentials=credentials)
            print("Google Drive API 서비스가 성공적으로 생성되었습니다.\n")
            return service
        
        except FileNotFoundError:
            print(f"오류: {self.credentials_path} 파일을 찾을 수 없습니다.")
            print("현재 디렉토리에 credentials.json 파일이 있는지 확인하세요.")
            raise
        except Exception as e:
            print(f"서비스 생성 중 오류 발생: {e}")
            raise
    
    def get_file_metadata(self, file_id):
        """
        파일 메타데이터 조회
        
        Args:
            file_id (str): Google Drive 파일 ID
            
        Returns:
            dict: 파일 메타데이터
        """
        try:
            # supportsAllDrives=True를 설정하여 Shared Drive 지원
            file = self.service.files().get(
                fileId=file_id,
                supportsAllDrives=True,
                fields='id, name, mimeType, createdTime, modifiedTime, owners, driveId'
            ).execute()
            
            return file
        
        except HttpError as error:
            print(f"파일 메타데이터 조회 중 오류 발생: {error}")
            return None
    
    def read_google_doc(self, file_id):
        """
        Google 문서(Docs) 내용을 텍스트로 읽기
        
        Args:
            file_id (str): Google Docs 파일 ID
            
        Returns:
            str: 문서 내용
        """
        try:
            # Google Docs를 plain text로 export
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType='text/plain'
            )
            
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"다운로드 진행률: {int(status.progress() * 100)}%")
            
            # 바이트를 문자열로 변환
            content = file_content.getvalue().decode('utf-8')
            return content
        
        except HttpError as error:
            print(f"문서 읽기 중 오류 발생: {error}")
            return None
    
    def read_google_sheet(self, file_id):
        """
        Google 스프레드시트를 CSV로 읽기
        
        Args:
            file_id (str): Google Sheets 파일 ID
            
        Returns:
            str: CSV 형식의 내용
        """
        try:
            # Google Sheets를 CSV로 export
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType='text/csv'
            )
            
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"다운로드 진행률: {int(status.progress() * 100)}%")
            
            content = file_content.getvalue().decode('utf-8')
            return content
        
        except HttpError as error:
            print(f"스프레드시트 읽기 중 오류 발생: {error}")
            return None
    
    def read_file_content(self, file_id):
        """
        파일 타입을 자동으로 감지하여 내용 읽기
        
        Args:
            file_id (str): Google Drive 파일 ID
            
        Returns:
            tuple: (파일명, 내용)
        """
        # 먼저 파일 메타데이터 조회
        metadata = self.get_file_metadata(file_id)
        
        if not metadata:
            return None, None
        
        file_name = metadata.get('name', 'Unknown')
        mime_type = metadata.get('mimeType', '')
        
        print(f"\n파일명: {file_name}")
        print(f"파일 타입: {mime_type}")
        
        # MIME 타입에 따라 적절한 읽기 메서드 선택
        if mime_type == 'application/vnd.google-apps.document':
            print("Google 문서로 감지됨")
            content = self.read_google_doc(file_id)
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            print("Google 스프레드시트로 감지됨")
            content = self.read_google_sheet(file_id)
        else:
            print(f"지원하지 않는 파일 타입입니다: {mime_type}")
            content = None
        
        return file_name, content
    
    def read_multiple_files(self, file_ids):
        """
        여러 파일의 내용을 한 번에 읽기
        
        Args:
            file_ids (list): Google Drive 파일 ID 리스트
            
        Returns:
            list: [(파일명, 내용), ...] 형태의 튜플 리스트
        """
        results = []
        total = len(file_ids)
        
        print(f"\n총 {total}개의 파일을 읽습니다...\n")
        
        for idx, file_id in enumerate(file_ids, 1):
            print(f"{'='*60}")
            print(f"[{idx}/{total}] 파일 읽는 중...")
            print(f"{'='*60}")
            
            try:
                file_name, content = self.read_file_content(file_id)
                results.append((file_name, content))
                
                if content:
                    print(f"✓ 성공: {len(content)} 글자")
                else:
                    print(f"✗ 실패: 파일을 읽을 수 없음")
                    
            except Exception as e:
                print(f"✗ 오류 발생: {e}")
                results.append((None, None))
        
        print(f"\n{'='*60}")
        print(f"완료: {total}개 파일 중 {sum(1 for _, c in results if c is not None)}개 성공")
        print(f"{'='*60}\n")
        
        return results
    
    def read_files(self, file_ids):
        """
        단일 파일 ID 또는 파일 ID 리스트를 받아서 처리
        
        Args:
            file_ids (str or list): 파일 ID 또는 파일 ID 리스트
            
        Returns:
            tuple or list: 
                - 단일 ID인 경우: (파일명, 내용)
                - 리스트인 경우: [(파일명, 내용), ...]
        """
        if isinstance(file_ids, str):
            # 단일 파일 ID
            return self.read_file_content(file_ids)
        elif isinstance(file_ids, list):
            # 파일 ID 리스트
            return self.read_multiple_files(file_ids)
        else:
            raise TypeError("file_ids는 문자열(str) 또는 리스트(list)여야 합니다.")
    
    def save_results_to_csv(self, results, output_file='output.csv', include_content=True):
        """
        읽은 결과를 CSV 파일로 저장
        
        Args:
            results (list): read_files 또는 read_multiple_files의 결과 [(파일명, 내용), ...]
            output_file (str): 저장할 CSV 파일명 (기본값: 'output.csv')
            include_content (bool): 내용 전체를 포함할지 여부 (기본값: True)
                                   False인 경우 내용 길이와 미리보기만 저장
        
        Returns:
            str: 저장된 파일 경로
        """
        import csv
        
        # 단일 결과를 리스트로 변환
        if isinstance(results, tuple) and len(results) == 2:
            results = [results]
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            if include_content:
                # 전체 내용 포함
                fieldnames = ['순번', '파일명', '상태', '내용_길이', '내용']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for idx, (file_name, content) in enumerate(results, 1):
                    writer.writerow({
                        '순번': idx,
                        '파일명': file_name if file_name else 'Unknown',
                        '상태': '성공' if content else '실패',
                        '내용_길이': len(content) if content else 0,
                        '내용': content if content else ''
                    })
            else:
                # 요약 정보만 포함
                fieldnames = ['순번', '파일명', '상태', '내용_길이', '미리보기']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for idx, (file_name, content) in enumerate(results, 1):
                    preview = content[:200] + '...' if content and len(content) > 200 else (content if content else '')
                    writer.writerow({
                        '순번': idx,
                        '파일명': file_name if file_name else 'Unknown',
                        '상태': '성공' if content else '실패',
                        '내용_길이': len(content) if content else 0,
                        '미리보기': preview
                    })
        
        print(f"\n✓ 결과를 {output_file}에 저장했습니다.")
        return output_file
    
    def save_to_separate_csv(self, results, output_dir='output_csv'):
        """
        각 파일의 내용을 개별 CSV 파일로 저장
        
        Args:
            results (list): read_files 또는 read_multiple_files의 결과 [(파일명, 내용), ...]
            output_dir (str): 저장할 디렉토리명 (기본값: 'output_csv')
        
        Returns:
            list: 저장된 파일 경로 리스트
        """
        import csv
        import os
        
        # 단일 결과를 리스트로 변환
        if isinstance(results, tuple) and len(results) == 2:
            results = [results]
        
        # 출력 디렉토리 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        saved_files = []
        
        for idx, (file_name, content) in enumerate(results, 1):
            if not content:
                print(f"✗ {file_name}: 내용이 없어 건너뜁니다.")
                continue
            
            # 안전한 파일명 생성
            safe_name = file_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            output_file = os.path.join(output_dir, f"{idx}_{safe_name}.csv")
            
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['파일명', file_name])
                writer.writerow(['내용_길이', len(content)])
                writer.writerow([])
                writer.writerow(['내용'])
                writer.writerow([content])
            
            saved_files.append(output_file)
            print(f"✓ {output_file}에 저장 완료")
        
        print(f"\n총 {len(saved_files)}개 파일을 {output_dir}/ 디렉토리에 저장했습니다.")
        return saved_files


def main():
    """메인 함수 - 사용 예제"""
    
    # 설정
    CREDENTIALS_PATH = 'credentials.json'  # 현재 디렉토리의 서비스 계정 JSON 파일
    
    # 예제 1: 단일 파일 읽기
    SINGLE_FILE_ID = 'your-file-id-here'
    
    # 예제 2: 여러 파일 읽기
    MULTIPLE_FILE_IDS = [
        'file-id-1',
        'file-id-2',
        'file-id-3'
    ]
    
    # GoogleDriveReader 인스턴스 생성
    reader = GoogleDriveReader(credentials_path=CREDENTIALS_PATH)
    
    # 방법 1: 단일 파일 읽기
    print("\n" + "="*60)
    print("예제 1: 단일 파일 읽기")
    print("="*60)
    file_name, content = reader.read_files(SINGLE_FILE_ID)
    if content:
        print(f"\n파일 '{file_name}'을 성공적으로 읽었습니다.")
    
    # 방법 2: 여러 파일 한 번에 읽기
    print("\n" + "="*60)
    print("예제 2: 여러 파일 읽기")
    print("="*60)
    results = reader.read_files(MULTIPLE_FILE_IDS)
    
    # 결과 처리
    for file_name, content in results:
        if content:
            print(f"✓ {file_name}: {len(content)} 글자")
        else:
            print(f"✗ 파일을 읽을 수 없음")
    
    # 방법 3: 결과를 CSV로 저장
    print("\n" + "="*60)
    print("예제 3: 결과를 CSV로 저장")
    print("="*60)
    reader.save_results_to_csv(results, output_file='results.csv', include_content=True)


if __name__ == "__main__":
    main()