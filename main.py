import os
import sys

import pandas as pd
from colorama import Fore
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']

# MS Office file extensions
EXTENSIONS = {
    'docx': 'application/vnd.google-apps.document',
    'xlsx': 'application/vnd.google-apps.spreadsheet',
    'pptx': 'application/vnd.google-apps.presentation',
}

FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'

FORBIDDEN_FOLDERS = ["Solutions", "Term Work"]


def list_files_in_folder_as_df(folder_id):
    """
    List all the files in the folder as a dataframe.
    :param folder_id: id of the folder.
    :return: a dataframe with the files in the folder.
    """
    return pd.DataFrame(
        service
        .files()
        .list(
            q="'{}' in parents and trashed=false".format(folder_id),
            fields="files(id, name, mimeType, parents)"
        )
        .execute().get('files', []))


def create_folder(name, parent_id):
    """
    Create a folder in the drive.
    :param name: name of the folder.
    :param parent_id: parent id in the drive.
    :return: id of the folder in the drive.
    """
    file_metadata = {'name': name, 'parents': [parent_id], 'mimeType': FOLDER_MIMETYPE}
    file = service.files().create(body=file_metadata, fields='id').execute()

    return file["id"]


def upload_file(file_path, file_type, parent_id, level):
    """
    Upload a file to the drive.
    :param file_path: file path.
    :param file_type: file type.
    :param parent_id: parent id in the drive.
    :param level: level of the file in the tree.
    :return: None.
    """
    name = file_path.split("\\")[-1]
    print(Fore.YELLOW + "{}Uploading {}".format(level * "\t", name))

    # check if file size is bigger than 5MB
    if os.path.getsize(file_path) > 5 * 1024 * 1024:
        print(Fore.RED + "{}File size is bigger than 5MB, uploading in chunks".format(level * "\t"))
        file_metadata, media = media_file_upload(file_path, file_type, name, parent_id)
        uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id',
                                               uploadType="resumable")

        # upload the file and print the progress
        response = None
        while response is None:
            status, response = uploaded_file.next_chunk()
            if status:
                print('{}Uploaded {}%.'.format(level * "\t", int(status.progress() * 100)))

        rename_office_file(file_type, name, uploaded_file)
    else:
        file_metadata, media = media_file_upload(file_path, file_type, name, parent_id)
        uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        rename_office_file(file_type, name, uploaded_file)
    print(Fore.GREEN + "{}Done\n".format(level * "\t"))


def rename_office_file(file_type, name, uploaded_file):
    """
    Rename the file if it is an MS Office file.
    :param file_type: file type.
    :param name: name of the file.
    :param uploaded_file: uploaded file.
    :return: None.
    """
    if file_type != "":
        file_metadata = {'name': os.path.splitext(name)[0]}
        service.files().update(fileId=uploaded_file['id'], body=file_metadata).execute()


def media_file_upload(file_path, file_type, name, parent_id):
    if file_type == "":
        file_metadata = {'name': name, 'parents': [parent_id]}
        media = MediaFileUpload(file_path, chunksize=1024 * 1024, resumable=True)
    else:
        file_metadata = {'name': name, 'parents': [parent_id], 'mimeType': file_type}
        media = MediaFileUpload(file_path, mimetype=file_type, chunksize=1024 * 1024, resumable=True)
    return file_metadata, media


def upload_recur(table, path, parent_id, level):
    """
    Upload recursively all the files in the folder, DFS algorithm is used.
    :param table: dataframe with the files in the folder in the drive.
    :param path: path of the folder in the local machine.
    :param parent_id: parent id in the drive.
    :param level: level of the file in the tree.
    :return: None.
    """
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if is_forbidden_folder(name):
            return

        # check if the file is a folder
        if os.path.isdir(file_path):
            print('\033[39m' + "{}{}".format(level * "\t", name))
            _, is_exist = exists(name, table)
            if is_exist:
                file_id = table[table["name"] == name]["id"].values[0]
            else:
                file_id = create_folder(name, parent_id)

            data_folder = list_files_in_folder_as_df(file_id)
            upload_recur(data_folder, file_path, file_id, level + 1)
        else:
            file_type, is_exist = exists(name, table)
            if not is_exist:
                upload_file(file_path, file_type, parent_id, level)


def exists(name, table):
    """
    Check if the file exists in the drive and if it is an MS Office file.
    :param name: name of the file.
    :param table: dataframe with the files in the folder in the drive.
    :return: The file type and True if the file exists, False otherwise.
    """
    file_type = os.path.splitext(name)[1][1:]

    # check if the file is an MS Office file
    if file_type in EXTENSIONS:
        file_type = EXTENSIONS[file_type]
        name_without_extension = os.path.splitext(name)[0]

        # filter table with the same name and the same file type
        rows = table[(table["name"] == name_without_extension) & (table["mimeType"] == file_type)]

        return file_type, not rows.empty
    else:
        file_type = ""

    return file_type, not table.empty and name in table["name"].values


def is_forbidden_folder(name):
    """
    Check if the folder is forbidden.
    :param name: name of the folder.
    :return: True if the folder is forbidden, False otherwise.
    """
    return name in FORBIDDEN_FOLDERS


def main(argv):
    drive_id = argv[1]
    origin_root = argv[2]

    data = list_files_in_folder_as_df(drive_id)

    print("\n")
    upload_recur(data, origin_root, drive_id, 0)
    print(Fore.LIGHTRED_EX + "\nEND")


if __name__ == "__main__":
    """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
    if len(sys.argv) != 3:
        print("Usage: python main.py <drive_id> <path>")
        exit(1)

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
    except HttpError as error:
        print('An error occurred: {}', error)
    main(sys.argv)
