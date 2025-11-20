#pip install pymongo
import os

from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil import parser
from googleapiclient.discovery import build
from google_drive_reader import GoogleDriveReader
from drive_flie_list import (
    authenticate_google_drive,
    get_files_in_date_range,
)
from pymongo import MongoClient

# MongoDB connection
load_dotenv()
ip = os.getenv('MONGO_IP')
user = os.getenv('MONGO_USER')
password = os.getenv('MONGO_PASSWORD')
database = os.getenv('MONGO_DATABASE')

print(ip, user, password, database)


client = MongoClient(
    ip,
    username=user,
    password=password,
    authSource=database
)

#check connection
print(client.list_database_names()) #return list of databases

creds = authenticate_google_drive()
service = build('drive', 'v3', credentials=creds)
reader = GoogleDriveReader()

def collect_files(shared_folder_id, s_date, e_date):
    collected_files = get_files_in_date_range(
        service,
        folder_id=shared_folder_id,
        start_date=s_date,
        end_date=e_date,
        search_type='created',
        file_types=['gdoc'],
        filename_keywords=['gemini'],
        recursive=True,
        debug=True
    )
    return collected_files

def collect_contents(collected_files):
    FILE_IDS_SHARED = [ file["id"] for file in collected_files ]
    reader = GoogleDriveReader()
    c_files_shared = reader.read_files(FILE_IDS_SHARED) #return list of tuples (filename, content)
    return c_files_shared

def add_contents_to_files(collected_files, c_files_shared):
    for i in range(len(collected_files)):
        if collected_files[i]["name"] == c_files_shared[i][0]:
            collected_files[i]["content"] = c_files_shared[i][1] # fill in content
    return collected_files


### mapping folder id to folder name which is created_by

def get_idmap(shared_files):
    parents_ids = []
    for i in range(len(shared_files)):
        fid = shared_files[i]["parents"][0] #parents folder id
        parents_ids.insert(0, fid)

    parents_tuple = tuple(parents_ids)

    idmap = {}
    for fid in parents_tuple:
        filename = reader.read_files(fid)[0]
        idmap[fid] = filename

    return idmap


def add_created_by_to_files(collected_files, idmap):
    for i in range(len(collected_files)):
        fid = collected_files[i]["parents"][0] #parents folder id
        collected_files[i]["created_by"] = idmap[fid] #fill in created_by
    return collected_files

def get_all_distict_ids():
    distinct_ids = client.shared.recordings.distinct("parents.0")
    return distinct_ids

def map_ids_to_names(distinct_ids):
    idmap = {}
    for fid in distinct_ids:
        filename = reader.read_files(fid)[0]
        idmap[fid] = filename
    return idmap

def update_created_by_in_mongo(distinct_ids, idmap):
    for fid in distinct_ids:
        client.shared.recordings.update_many(
            {"parents.0": fid},
            {"$set": {"created_by": idmap[fid]}}
        )
    print(f"Updated {len(distinct_ids)} documents")

def get_documents_datetime_after(query_date, collection):
    query_date = parser.parse(query_date).isoformat()
    result = collection.find({"createdTime": {"$gt": query_date}}, {"id": 1, "createdTime": 1, "name": 1, "created_by": 1})
    return result.to_list()

def delete_documents_datetime_after(query_date, collection):
    query_date = parser.parse(query_date).isoformat()
    query = {"createdTime": {"$gt": query_date}}
    result = collection.delete_many(query)
    print(f"Deleted {result.deleted_count} documents")
    return result.deleted_count

def insert_documents_to_mongo(documents, collection):
    collection.insert_many(documents)
    print(f"Inserted {len(documents)} documents")
    return len(documents)

if __name__ == "__main__":

    shared_folder_id = os.getenv('SHARED_FOLDER_ID')
    irene_folder_id = os.getenv('IRENE_FOLDER_ID')
    jaden_folder_id = os.getenv('JADEN_FOLDER_ID')
    kevin_folder_id = os.getenv('KEVIN_FOLDER_ID')

    # get_date_1_days_ago = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d') #'2025-11-19'
    # get_date_2_days_ago = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d') #'2025-11-18'
    
    today = datetime.now().strftime('%Y-%m-%d') 
    
    # 실행기록
    # '2025-11-19' 까지

    start_date = today # 00:00:00 GMT
    end_date = today # 23:59:59 GMT

    folder_list = [shared_folder_id, irene_folder_id, jaden_folder_id, kevin_folder_id]
    
    # collection_list = [client.shared.recordings, client.irene.recordings, client.jaden.recordings, client.kevin.recordings]
    
    # for test
    collection_list = [client.test_database.recordings, client.test_database.recordings, client.test_database.recordings, client.test_database.recordings]
    
    collection_dict = dict(zip(folder_list, collection_list))

    files_dict = {}

    #collect files from each folder
    for folder_id, collection in collection_dict.items():
        collected_files = collect_files(folder_id, start_date, end_date)
        c_files_shared = collect_contents(collected_files) #return list of tuples (filename, content)
        collected_files = add_contents_to_files(collected_files, c_files_shared) #fill in content
        if folder_id == shared_folder_id: #only for shared folder
            idmap = get_idmap(collected_files) #return dict of folder id to folder name
            collected_files = add_created_by_to_files(collected_files, idmap) #fill in created_by
        files_dict[folder_id] = collected_files

    #insert files to mongo
    for folder_id, files in files_dict.items():
        collection = collection_dict[folder_id]
        if len(files) > 0:
            print(f"Inserting {len(files)} documents to {collection.full_name}")
            insert_documents_to_mongo(files, collection)
        else:
            print(f"No documents to insert to {collection.full_name}")



# combine shared_files and c_files_shared
# for i in range(len(shared_files)):
#     if shared_files[i]["name"] == c_files_shared[i][0]:
#         shared_files[i]["content"] = c_files_shared[i][1] # fill in content
        
#         fid = shared_files[i]["parents"][0] #parents folder id
#         parent_folder_name = reader.read_files(fid)[0] #parents folder name
#         shared_files[i]["created_by"] = shared_files[0]["parents"][0] #fill in created_by


# client.shared.recordings.insert_many(shared_files)




#add new values to mongo document where document.parents[0] matches idmap's key
# db = client.shared
# collection = db.recordings

# Update documents where parents[0] matches idmap's key
# for folder_id, person_name in idmap.items():
#     result = collection.update_many(
#         {"parents.0": folder_id},  # Match documents where parents[0] equals folder_id
#         {"$set": {"created_by": person_name}}  # Set created_by field to person_name
#     )
#     print(f"Updated {result.modified_count} documents for {person_name} (folder_id: {folder_id})")

# print(f"\n✓ All documents updated with created_by field based on idmap")