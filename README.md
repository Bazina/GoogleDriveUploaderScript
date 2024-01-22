# Google Drive Uploader Script

A Python script to upload files and folders to Google Drive. Integrated with Google Drive API v3.

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Google Drive Setup](#google-drive-setup)
6. [Usage](#usage)
7. [Contributing](#contributing)

## Introduction

This script enables you to upload files and folders to Google Drive using Python. It supports uploading various file types, including Google Docs, Sheets, and Presentations.

## Features

- Upload files to Google Drive with optional chunked upload for large files.
- Create folders in Google Drive.
- Recursively upload all files in a folder.

## Prerequisites

Before using this script, ensure you have the following

- Python installed on your machine.
- Access to the Google Drive API (credentials.json file).
- Necessary Python libraries installed (colorama, pandas, google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client).

> **Note**
> - This script was tested on Python 3.10.

## Installation

1. Clone this repository

   ```bash
   git clone https://github.com/Bazina/GoogleDriveUploaderScript.git
   ```

2. Install dependencies

   ```bash
   cd GoogleDriveUploaderScript
   pip install -r requirements.txt
   ```

## Google Drive Setup

1. Set up a Google Cloud Project and enable the Google Drive API.
2. Create an OAuth consent screen (desktop application) with the required scopes.
   - `https://www.googleapis.com/auth/drive`
3. Put the server domain in the Authorized Domains section.
4. Create a OAuth 2.0 Client ID and download the credentials file (you can leave the Authorized JavaScript origins blank).
5. Download the credentials file and rename it to `credentials.json`.
6. Run the script using Python and follow the instructions to authenticate with Google Drive. A `token.json` file will be created.

## Usage

1. Pass the `origin_root` and `drive_id` as arguments to the script with your local folder path and Google Drive folder ID.
2. Run the script:

   ```bash
   python main.py <origin_root> <drive_id>
   ```

3. The script will upload files and folders to the specified Google Drive folder.

## Contributing

Contributions are welcomed! Fork the repository, make changes, and submit a pull request.