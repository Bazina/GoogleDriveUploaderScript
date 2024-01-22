import os

import pandas as pd
from colorama import Fore
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']


def list_files_in_folder_as_df(folder_id):
    return pd.DataFrame(
        service
        .files()
        .list(
            q="'{}' in parents and trashed=false".format(folder_id),
            fields="files(id, name, mimeType, parents)"
        )
        .execute().get('files', []))


def create_folder(name, parent_id):
    file_metadata = {'name': name, 'parents': [parent_id], 'mimeType': 'application/vnd.google-apps.folder'}

    file = service.files().create(body=file_metadata, fields='id').execute()

    return file["id"]


def upload_file(file_path, parent_id, level):
    name = file_path.split("\\")[-1]
    print(Fore.YELLOW + "{}Uploading {}".format(level * "\t", name))
    file_metadata = {'name': name, 'parents': [parent_id]}

    # check if file size is bigger than 5MB
    if os.path.getsize(file_path) > 5 * 1024 * 1024:
        print(Fore.RED + "{}File size is bigger than 5MB, uploading in chunks".format(level * "\t"))
        media = MediaFileUpload(file_path, chunksize=1024 * 1024, resumable=True)
        request = service.files().create(body=file_metadata, media_body=media, fields='id', uploadType="resumable")

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print('{}Uploaded {}%.'.format(level * "\t", int(status.progress() * 100)))
    else:
        media = MediaFileUpload(file_path, resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(Fore.GREEN + "{}Done\n".format(level * "\t"))


def upload_recur(table, path, parent_id, level):
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if name == "Solutions" or name == "Term Work":
            return

        if os.path.isdir(file_path):
            print('\033[39m' + "{}{}".format(level * "\t", name))
            if table.empty or name not in table["name"].values:
                file_id = create_folder(name, parent_id)
            else:
                file_id = table[table["name"] == name]["id"].values[0]

            data_folder = list_files_in_folder_as_df(file_id)
            upload_recur(data_folder, file_path, file_id, level + 1)
        else:
            if table.empty or name not in table["name"].values:
                upload_file(file_path, parent_id, level)


def main():
    origin_root = "D:\\Library\\Faculty of Engineering\\Year 4\\1st Semester\\"

    drive_id = "1yp5kU3_wpWmzYuONLx3t4XXX8bC9bsbq"

    data = list_files_in_folder_as_df(drive_id)

    print("\n")
    upload_recur(data, origin_root, drive_id, 0)
    print(Fore.LIGHTRED_EX + "\nEND")


if __name__ == "__main__":
    """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
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
        # TODO(developer) - Handle errors from drive API.
        print('An error occurred: {error}')
    main()
