"""
CSV 저장 기능 예제

실행 방법:
python csv_example.py
"""

from google_drive_reader import GoogleDriveReader


def example_save_to_single_csv():
    """여러 파일을 하나의 CSV로 저장하는 예제"""
    print("="*60)
    print("예제 1: 여러 파일을 하나의 CSV로 저장")
    print("="*60)
    
    # FILE_IDS = [
    #     'file-id-1',
    #     'file-id-2',
    #     'file-id-3'
    # ]

    FILE_IDS = [
        'file-id-1',
        'file-id-2',
        'file-id-3',
        'file-id-4',
        'file-id-5'
    ]
    
    reader = GoogleDriveReader()
    
    # 파일 읽기
    results = reader.read_files(FILE_IDS)
    
    # CSV로 저장 (전체 내용 포함)
    reader.save_results_to_csv(results, output_file='results_full.csv', include_content=True)
    
    print("\n✓ results_full.csv 파일을 확인하세요!")


def example_save_summary_csv():
    """요약 정보만 CSV로 저장하는 예제"""
    print("\n" + "="*60)
    print("예제 2: 요약 정보만 CSV로 저장")
    print("="*60)
    
    FILE_IDS = [
        'file-id-1',
        'file-id-2',
        'file-id-3',
        'file-id-4',
        'file-id-5'
    ]
    
    reader = GoogleDriveReader()
    results = reader.read_files(FILE_IDS)
    
    # CSV로 저장 (요약 정보만 - 미리보기 200자)
    reader.save_results_to_csv(results, output_file='results_summary.csv', include_content=False)
    
    print("\n✓ results_summary.csv 파일을 확인하세요!")
    print("  - 파일명, 상태, 내용 길이, 미리보기(200자)가 포함됩니다.")


def example_save_to_separate_csv():
    """각 파일을 개별 CSV로 저장하는 예제"""
    print("\n" + "="*60)
    print("예제 3: 각 파일을 개별 CSV로 저장")
    print("="*60)
    
    FILE_IDS = [
        'file-id-1',
        'file-id-2',
        'file-id-3'
    ]
    
    reader = GoogleDriveReader()
    results = reader.read_files(FILE_IDS)
    
    # 각 파일을 개별 CSV로 저장
    saved_files = reader.save_to_separate_csv(results, output_dir='output_csv')
    
    print(f"\n✓ output_csv/ 디렉토리에 {len(saved_files)}개 파일이 저장되었습니다!")


def example_single_file_to_csv():
    """단일 파일을 CSV로 저장하는 예제"""
    print("\n" + "="*60)
    print("예제 4: 단일 파일을 CSV로 저장")
    print("="*60)
    
    FILE_ID = 'your-file-id-here'
    
    reader = GoogleDriveReader()
    
    # 단일 파일 읽기
    result = reader.read_files(FILE_ID)
    
    # CSV로 저장
    reader.save_results_to_csv(result, output_file='single_file.csv', include_content=True)
    
    print("\n✓ single_file.csv 파일을 확인하세요!")


def example_custom_workflow():
    """커스텀 워크플로우 - 읽고, 처리하고, CSV로 저장"""
    print("\n" + "="*60)
    print("예제 5: 커스텀 워크플로우")
    print("="*60)
    
    FILE_IDS = [
        'file-id-1',
        'file-id-2',
        'file-id-3',
        'file-id-4'
    ]
    
    reader = GoogleDriveReader()
    results = reader.read_files(FILE_IDS)
    
    # 1. 전체 결과를 요약 CSV로 저장
    print("\n1단계: 전체 결과 요약 저장")
    reader.save_results_to_csv(results, output_file='all_results_summary.csv', include_content=False)
    
    # 2. 성공한 파일만 필터링
    successful_results = [(name, content) for name, content in results if content]
    
    print(f"\n2단계: 성공한 파일 {len(successful_results)}개만 필터링")
    
    # 3. 성공한 파일의 전체 내용을 CSV로 저장
    if successful_results:
        reader.save_results_to_csv(
            successful_results, 
            output_file='successful_results_full.csv', 
            include_content=True
        )
    
    # 4. 각 파일을 개별 CSV로도 저장
    print("\n3단계: 각 파일을 개별 CSV로 저장")
    reader.save_to_separate_csv(successful_results, output_dir='successful_files_csv')
    
    print("\n✓ 모든 단계 완료!")
    print("  - all_results_summary.csv: 모든 파일 요약")
    print("  - successful_results_full.csv: 성공한 파일의 전체 내용")
    print("  - successful_files_csv/: 각 파일의 개별 CSV")


def example_with_pandas():
    """pandas를 사용하여 더 복잡한 CSV 처리 (선택사항)"""
    print("\n" + "="*60)
    print("예제 6: pandas를 사용한 고급 CSV 처리")
    print("="*60)
    
    try:
        import pandas as pd
        
        FILE_IDS = [
            'file-id-1',
            'file-id-2',
            'file-id-3'
        ]
        
        reader = GoogleDriveReader()
        results = reader.read_files(FILE_IDS)
        
        # pandas DataFrame으로 변환
        data = []
        for idx, (file_name, content) in enumerate(results, 1):
            data.append({
                '순번': idx,
                '파일명': file_name if file_name else 'Unknown',
                '상태': '성공' if content else '실패',
                '내용_길이': len(content) if content else 0,
                '단어_수': len(content.split()) if content else 0,
                '줄_수': len(content.split('\n')) if content else 0,
                '첫_100자': content[:100] if content else ''
            })
        
        df = pd.DataFrame(data)
        
        # CSV로 저장
        df.to_csv('results_pandas.csv', index=False, encoding='utf-8-sig')
        
        print("\n✓ pandas를 사용하여 results_pandas.csv에 저장했습니다!")
        print("\nDataFrame 미리보기:")
        print(df[['순번', '파일명', '상태', '내용_길이', '단어_수', '줄_수']])
        
    except ImportError:
        print("\n✗ pandas가 설치되어 있지 않습니다.")
        print("설치하려면: pip install pandas")


if __name__ == "__main__":
    print("\nGoogle Drive 결과를 CSV로 저장하는 예제\n")
    
    # 사용하려는 예제의 주석을 해제하세요
    
    # 예제 1: 여러 파일을 하나의 CSV로 저장
    # example_save_to_single_csv()
    
    # 예제 2: 요약 정보만 CSV로 저장
    # example_save_summary_csv()
    
    # 예제 3: 각 파일을 개별 CSV로 저장
    # example_save_to_separate_csv()
    
    # 예제 4: 단일 파일을 CSV로 저장
    # example_single_file_to_csv()
    
    # 예제 5: 커스텀 워크플로우
    # example_custom_workflow()
    
    # 예제 6: pandas를 사용한 고급 CSV 처리
    # example_with_pandas()

    
    
    print("\n" + "="*60)
    print("사용하려는 예제 함수의 주석을 해제하고 실행하세요")
    print("각 예제에서 FILE_ID 또는 FILE_IDS를 실제 값으로 변경하세요")
    print("="*60 + "\n")

    example_save_to_single_csv()