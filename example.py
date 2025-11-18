from googleapiclient.discovery import build

from drive_flie_list import (
    authenticate_google_drive,
    get_files_in_date_range,
    # format_file_info
)

from google_drive_reader import GoogleDriveReader

creds = authenticate_google_drive()
service = build('drive', 'v3', credentials=creds)

folder_recordings_collected = 'Enter your folder ID here'  # Enter your folder ID here

l_files = get_files_in_date_range(
    service,
    folder_id=folder_recordings_collected,
    start_date='2025-11-10',  # 7 days ago
    end_date='2025-11-17',    # Today
    search_type='created', # used created date to search
    file_types=['gdoc'],  # gdoc only
    filename_keywords=['gemini'],
    recursive=True,  # Set True to search subfolders
    debug=True  # Print debug info
)

# see all file names
# for file in l_files:
#     print(file["name"])

# files[0] ->
# 
# {'parents': ['1DE2SahSPqJAmCJpSBy5voNPQg_aaaaaa'],
#  'id': '1lvWZJDodFWQmpw_YYduwVyrWjnILr_aaaaaaaaaaa',
#  'name': 'aaaaacall – 2025/11/17 09:22 GMT – Notes by Gemini',
#  'mimeType': 'application/vnd.google-apps.document',
#  'webViewLink': 'https://docs.google.com/document/d/1lvWZJDodFWQmpw_YYduwVyrWjnILr_aaaaaaaaaaa/edit?usp=drivesdk',
#  'createdTime': '2025-11-17T10:17:47.Z',
#  'modifiedTime': '2025-11-17T11:03:07.Z',
#  'driveId': '0AK6W4i0aaaaaaa',
#  'size': '245'}

FILE_IDS = [ file["id"] for file in l_files ]

reader = GoogleDriveReader()
c_files = reader.read_files(FILE_IDS)

#content_files = [(filename, contents), ... ]

reader.save_results_to_csv(c_files, output_file='results_full_irene.csv', include_content=True)

