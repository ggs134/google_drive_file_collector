"""
Google Drive File List Extraction Script (Enhanced Version)
Extract list of files created/modified during a specific period.
Improved folder search and debugging features.
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import os
from datetime import datetime, timedelta
import pandas as pd

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_google_drive():
    """Authenticate with Google Drive API"""
    creds = None
    
    # Load existing credentials if available
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Login if no valid credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def verify_folder_access(service, folder_id):
    """
    Verify folder access and return folder information
    
    Args:
        service: Google Drive API service object
        folder_id: Folder ID to verify
        
    Returns:
        Folder information dictionary or None
    """
    try:
        # Removed permissions field to avoid permission issues
        # Added supportsAllDrives for Shared Drive support
        folder = service.files().get(
            fileId=folder_id,
            fields='id, name, mimeType, owners, shared, driveId',
            supportsAllDrives=True
        ).execute()
        
        print(f"\n✓ Folder Access Verified:")
        print(f"  - Folder Name: {folder.get('name')}")
        print(f"  - Folder ID: {folder.get('id')}")
        print(f"  - Type: {folder.get('mimeType')}")
        print(f"  - Owner: {folder.get('owners', [{}])[0].get('emailAddress', 'N/A') if folder.get('owners') else 'N/A'}")
        print(f"  - Shared: {folder.get('shared', False)}")
        
        # Check if it's a Shared Drive
        if folder.get('driveId'):
            print(f"  - Shared Drive: Yes (Drive ID: {folder.get('driveId')})")
        else:
            print(f"  - Shared Drive: No")
        
        if folder.get('mimeType') != 'application/vnd.google-apps.folder':
            print(f"  ⚠ Warning: This is not a folder!")
            
        return folder
    except Exception as error:
        # Using Exception instead of HttpError for broader error handling
        print(f"\n✗ Folder Access Failed:")
        print(f"  - Error: {error}")
        print(f"  - Please verify the folder ID and access permissions.")
        return None

def get_all_subfolders(service, folder_id):
    """
    Recursively get all subfolder IDs within a specific folder
    
    Args:
        service: Google Drive API service object
        folder_id: Parent folder ID
        
    Returns:
        List of subfolder IDs
    """
    subfolders = []
    page_token = None
    
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    
    while True:
        try:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name)',
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            folders = response.get('files', [])
            
            for folder in folders:
                subfolders.append(folder['id'])
                # Recursively search subfolders
                subfolders.extend(get_all_subfolders(service, folder['id']))
            
            page_token = response.get('nextPageToken')
            if not page_token:
                break
                
        except Exception as error:
            print(f"Error searching subfolders: {error}")
            break
    
    return subfolders

def build_file_type_query(file_types):
    """
    Build search query from file type list
    
    Args:
        file_types: List of file types (e.g., ['pdf', 'docx', 'image', 'video'])
    
    Returns:
        MIME type query string
    """
    # MIME type mapping by file type
    mime_type_map = {
        # Documents
        'pdf': "mimeType='application/pdf'",
        'doc': "mimeType='application/msword'",
        'docx': "mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
        'txt': "mimeType='text/plain'",
        'rtf': "mimeType='application/rtf'",
        
        # Spreadsheets
        'xls': "mimeType='application/vnd.ms-excel'",
        'xlsx': "mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
        'csv': "mimeType='text/csv'",
        
        # Presentations
        'ppt': "mimeType='application/vnd.ms-powerpoint'",
        'pptx': "mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation'",
        
        # Google Workspace files
        'gdoc': "mimeType='application/vnd.google-apps.document'",
        'gsheet': "mimeType='application/vnd.google-apps.spreadsheet'",
        'gslide': "mimeType='application/vnd.google-apps.presentation'",
        'gform': "mimeType='application/vnd.google-apps.form'",
        'gdrawing': "mimeType='application/vnd.google-apps.drawing'",
        
        # Images (comprehensive)
        'image': "mimeType contains 'image/'",
        'jpg': "mimeType='image/jpeg'",
        'jpeg': "mimeType='image/jpeg'",
        'png': "mimeType='image/png'",
        'gif': "mimeType='image/gif'",
        'bmp': "mimeType='image/bmp'",
        'svg': "mimeType='image/svg+xml'",
        'webp': "mimeType='image/webp'",
        
        # Videos (comprehensive)
        'video': "mimeType contains 'video/'",
        'mp4': "mimeType='video/mp4'",
        'avi': "mimeType='video/x-msvideo'",
        'mov': "mimeType='video/quicktime'",
        'wmv': "mimeType='video/x-ms-wmv'",
        
        # Audio (comprehensive)
        'audio': "mimeType contains 'audio/'",
        'mp3': "mimeType='audio/mpeg'",
        'wav': "mimeType='audio/wav'",
        
        # Archives
        'zip': "mimeType='application/zip'",
        'rar': "mimeType='application/x-rar-compressed'",
        '7z': "mimeType='application/x-7z-compressed'",
        'tar': "mimeType='application/x-tar'",
        'gz': "mimeType='application/gzip'",
        
        # Others
        'json': "mimeType='application/json'",
        'xml': "mimeType='application/xml'",
        'html': "mimeType='text/html'",
        'css': "mimeType='text/css'",
        'js': "mimeType='application/javascript'",
        'py': "mimeType='text/x-python'",
    }
    
    queries = []
    for file_type in file_types:
        file_type_lower = file_type.lower()
        if file_type_lower in mime_type_map:
            queries.append(mime_type_map[file_type_lower])
        else:
            # Search by extension directly
            queries.append(f"name contains '.{file_type_lower}'")
    
    return ' or '.join(queries) if queries else None

def filter_by_exclude_keywords(files, exclude_keywords):
    """
    Filter files containing exclude keywords
    
    Args:
        files: List of files
        exclude_keywords: List of keywords to exclude
    
    Returns:
        Filtered file list
    """
    if not exclude_keywords:
        return files
    
    filtered_files = []
    for file in files:
        filename = file.get('name', '').lower()
        should_exclude = False
        
        for keyword in exclude_keywords:
            if keyword.lower() in filename:
                should_exclude = True
                break
        
        if not should_exclude:
            filtered_files.append(file)
    
    return filtered_files

def get_files_in_date_range(service, folder_id=None, start_date=None, end_date=None, 
                            search_type='modified', recursive=False, debug=False,
                            file_types=None, filename_keywords=None, exclude_keywords=None):
    """
    Get list of files created or modified during a specific period
    
    Args:
        service: Google Drive API service object
        folder_id: Folder ID to search (searches entire drive if None)
        start_date: Start date (datetime object or 'YYYY-MM-DD' string)
        end_date: End date (datetime object or 'YYYY-MM-DD' string)
        search_type: 'created' (by creation date) or 'modified' (by modification date)
        recursive: If True, recursively search subfolders
        debug: If True, print debug information
        file_types: List of file types to filter (e.g., ['pdf', 'docx', 'image'])
        filename_keywords: List of keywords that must be in filename (OR condition)
        exclude_keywords: List of keywords to exclude from filename
    
    Returns:
        List of file information
    """
    
    # Parse dates
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Set defaults (last 7 days)
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=7)
    
    # Convert to RFC 3339 format
    start_date_str = start_date.strftime('%Y-%m-%dT00:00:00')
    end_date_str = end_date.strftime('%Y-%m-%dT23:59:59')
    
    # Select field based on search type
    time_field = 'modifiedTime' if search_type == 'modified' else 'createdTime'
    
    print(f"\nSearch Criteria:")
    print(f"  - Period: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"  - Search By: {'Modified Date' if search_type == 'modified' else 'Created Date'}")
    
    # Print filter conditions
    if file_types:
        print(f"  - File Type Filter: {', '.join(file_types)}")
    if filename_keywords:
        print(f"  - Filename Keywords: {', '.join(filename_keywords)}")
    if exclude_keywords:
        print(f"  - Exclude Keywords: {', '.join(exclude_keywords)}")
    
    # Verify folder
    if folder_id:
        folder_info = verify_folder_access(service, folder_id)
        if not folder_info:
            return []
    
    # Collect all subfolder IDs if recursive search
    folders_to_search = []
    if folder_id:
        if recursive:
            print(f"\nSearching subfolders...")
            subfolders = get_all_subfolders(service, folder_id)
            folders_to_search = [folder_id] + subfolders
            print(f"  - Total {len(folders_to_search)} folders to search")
        else:
            folders_to_search = [folder_id]
            print(f"  - Searching specified folder only")
    
    all_results = []
    
    # Search by folder
    if folders_to_search:
        for idx, fid in enumerate(folders_to_search, 1):
            query_parts = [
                f"{time_field} >= '{start_date_str}'",
                f"{time_field} <= '{end_date_str}'",
                "trashed = false",
                f"'{fid}' in parents"
            ]
            
            # Add file type filter
            if file_types:
                type_queries = build_file_type_query(file_types)
                if type_queries:
                    query_parts.append(f"({type_queries})")
            
            # Add filename keyword filter
            if filename_keywords:
                name_queries = []
                for keyword in filename_keywords:
                    name_queries.append(f"name contains '{keyword}'")
                query_parts.append(f"({' or '.join(name_queries)})")
            
            query = ' and '.join(query_parts)
            
            if debug:
                print(f"\nSearching folder {idx}/{len(folders_to_search)}...")
                print(f"Query: {query}")
            
            results = execute_search(service, query, debug)
            all_results.extend(results)
            
            if debug and results:
                print(f"  → Found {len(results)} files")
    else:
        # Search entire drive
        print(f"\nSearching entire drive...")
        query_parts = [
            f"{time_field} >= '{start_date_str}'",
            f"{time_field} <= '{end_date_str}'",
            "trashed = false"
        ]
        
        # Add file type filter
        if file_types:
            type_queries = build_file_type_query(file_types)
            if type_queries:
                query_parts.append(f"({type_queries})")
        
        # Add filename keyword filter
        if filename_keywords:
            name_queries = []
            for keyword in filename_keywords:
                name_queries.append(f"name contains '{keyword}'")
            query_parts.append(f"({' or '.join(name_queries)})")
        
        query = ' and '.join(query_parts)
        
        if debug:
            print(f"Query: {query}")
        
        all_results = execute_search(service, query, debug)
    
    # Remove duplicates (same file may appear multiple times in recursive search)
    seen = set()
    unique_results = []
    for file in all_results:
        if file['id'] not in seen:
            seen.add(file['id'])
            unique_results.append(file)
    
    # Filter by exclude keywords (post-processing since API queries can't exclude easily)
    if exclude_keywords:
        before_count = len(unique_results)
        unique_results = filter_by_exclude_keywords(unique_results, exclude_keywords)
        excluded_count = before_count - len(unique_results)
        if debug and excluded_count > 0:
            print(f"\n{excluded_count} files filtered by exclude keywords")
    
    return unique_results

def execute_search(service, query, debug=False):
    """
    Execute query and get file list
    
    Args:
        service: Google Drive API service object
        query: Search query string
        debug: Debug mode
        
    Returns:
        List of file information
    """
    results = []
    page_token = None
    
    try:
        while True:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink, owners, parents, driveId)',
                pageToken=page_token,
                pageSize=1000,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            files = response.get('files', [])
            results.extend(files)
            
            page_token = response.get('nextPageToken')
            if not page_token:
                break
                
    except Exception as error:
        # Using Exception instead of HttpError for all error handling
        print(f"Error during search: {error}")
    
    return results

def format_file_info(files):
    """Format file information for readability"""
    formatted_files = []
    
    for file in files:
        # Convert size to readable format
        size_bytes = file.get('size', 'N/A')
        if size_bytes != 'N/A':
            size_bytes = int(size_bytes)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        else:
            size_str = 'N/A'
        
        formatted_file = {
            'File Name': file.get('name', ''),
            'File ID': file.get('id', ''),
            'File Type': file.get('mimeType', ''),
            'Created': file.get('createdTime', ''),
            'Modified': file.get('modifiedTime', ''),
            'Size': size_str,
            'Size (bytes)': file.get('size', 'N/A'),
            'Link': file.get('webViewLink', ''),
            'Owner': file.get('owners', [{}])[0].get('emailAddress', '') if file.get('owners') else '',
            'Parent Folder ID': ','.join(file.get('parents', [])),
            'Shared Drive ID': file.get('driveId', '')
        }
        formatted_files.append(formatted_file)
    
    return formatted_files

def save_to_excel(files, output_filename='google_drive_files.xlsx'):
    """Save file list to Excel"""
    df = pd.DataFrame(files)
    df.to_excel(output_filename, index=False, engine='openpyxl')
    print(f"\n✓ File list saved to '{output_filename}'.")

def save_to_csv(files, output_filename='google_drive_files.csv'):
    """Save file list to CSV"""
    df = pd.DataFrame(files)
    df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"\n✓ File list saved to '{output_filename}'.")

def main():
    """Main function"""
    
    # Authenticate Google Drive
    print("=" * 60)
    print("Google Drive File List Extraction Tool")
    print("=" * 60)
    print("\nAuthenticating Google Drive...")
    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)
    
    # ===== Usage Examples =====
    
    # Example 1: Files modified in last 7 days (entire drive)
    # files = get_files_in_date_range(service, search_type='modified', debug=True)
    
    # Example 2: Files modified in specific folder in last 30 days
    folder_id = '1xlSoJT8yBGi1h-Ps9aBWln6lG3uANxQX'  # Enter your folder ID here
    files = get_files_in_date_range(
        service,
        folder_id=folder_id,
        start_date='2025-11-10',  # 30 days ago
        end_date='2025-11-17',    # Today
        search_type='created',
        file_types=['gdoc'],  # gdoc only
        filename_keywords=['gemini'],
        recursive=True,  # Set True to search subfolders
        debug=True  # Print debug info
    )
    
    # Example 3: Search PDF files only
    # files = get_files_in_date_range(
    #     service,
    #     folder_id=folder_id,
    #     start_date='2024-11-01',
    #     end_date='2024-11-17',
    #     search_type='modified',
    #     file_types=['pdf'],  # PDF only
    #     debug=True
    # )
    
    # Example 4: Search images and videos only
    # files = get_files_in_date_range(
    #     service,
    #     folder_id=folder_id,
    #     start_date='2024-11-01',
    #     end_date='2024-11-17',
    #     search_type='modified',
    #     file_types=['image', 'video'],  # Images and videos
    #     debug=True
    # )
    
    # Example 5: Search files with specific keywords in filename
    # files = get_files_in_date_range(
    #     service,
    #     folder_id=folder_id,
    #     start_date='2024-11-01',
    #     end_date='2024-11-17',
    #     search_type='modified',
    #     filename_keywords=['report', 'summary'],  # Contains 'report' OR 'summary'
    #     debug=True
    # )
    
    # Example 6: Combine file type + keyword filters
    # files = get_files_in_date_range(
    #     service,
    #     folder_id=folder_id,
    #     start_date='2024-11-01',
    #     end_date='2024-11-17',
    #     search_type='modified',
    #     file_types=['pdf', 'docx'],  # PDF and DOCX only
    #     filename_keywords=['2024'],  # Filename contains '2024'
    #     exclude_keywords=['draft', 'temp'],  # Exclude 'draft' or 'temp'
    #     debug=True
    # )
    
    # Example 7: Search Google Workspace files only
    # files = get_files_in_date_range(
    #     service,
    #     folder_id=folder_id,
    #     start_date='2024-11-01',
    #     end_date='2024-11-17',
    #     search_type='modified',
    #     file_types=['gdoc', 'gsheet', 'gslide'],  # Google Docs, Sheets, Slides
    #     debug=True
    # )
    
    if not files:
        print("\nNo files found matching the criteria.")
        print("\nPlease check:")
        print("  1. Is the folder ID correct?")
        print("  2. Do you have access to the folder?")
        print("  3. Is the date range correct?")
        return
    
    print(f"\n" + "=" * 60)
    print(f"Found {len(files)} files")
    print("=" * 60)
    
    # Format file information
    formatted_files = format_file_info(files)
    
    # Print first 5 files to console
    print("\nFirst 5 files:")
    for i, file in enumerate(formatted_files[:5], 1):
        print(f"\n{i}. {file['File Name']}")
        print(f"   Created: {file['Created']}")
        print(f"   Modified: {file['Modified']}")
        print(f"   Size: {file['Size']}")
        print(f"   Type: {file['File Type']}")
        print(f"   Link: {file['Link']}")
    
    # Save to Excel file
    save_to_excel(formatted_files)
    
    # Uncomment to save to CSV as well
    # save_to_csv(formatted_files)

if __name__ == '__main__':
    main()
