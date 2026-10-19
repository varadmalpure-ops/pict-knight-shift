#!/usr/bin/env python3
"""
gdrive_sync.py - Google Drive Sync Engine for PICT Knight Shift

Uploads daily puzzles, board images, poll options, and solutions directly
to a dedicated Google Drive folder so club admins can pick them up directly
from the Google Drive mobile app on their phone.
"""

import os
import sys
import json
import mimetypes
import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

# Permissions: drive.file only manages files created by this app (secure & safe)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
ROOT_FOLDER_NAME = "PICT Knight Shift - WhatsApp Puzzles"


def print_setup_guide():
    """Prints a simple 4-step setup guide for obtaining credentials.json."""
    print("=" * 70)
    print("  🔑 GOOGLE DRIVE API SETUP GUIDE (Takes ~2 minutes)")
    print("=" * 70)
    print("1. Go to Google Cloud Console:")
    print("   👉 https://console.cloud.google.com/")
    print("\n2. Create a new project (or select existing):")
    print("   Click 'Select a project' at the top -> 'New Project' -> Name it 'PICT Knight Shift'")
    print("\n3. Enable the Google Drive API:")
    print("   In the search bar, search for 'Google Drive API' -> Click 'Enable'")
    print("\n4. Configure OAuth Consent Screen & Download credentials.json:")
    print("   a. Go to 'APIs & Services' -> 'OAuth consent screen'")
    print("   b. Select 'External' -> App name: 'PICT Knight Shift' -> fill your email -> Save")
    print("   c. Under 'Test users', add your Google email address.")
    print("   d. Go to 'Credentials' -> Click '+ CREATE CREDENTIALS' -> 'OAuth client ID'")
    print("   e. Application type: Select 'Desktop app' -> Name: 'PICT Desktop Sync' -> Create")
    print("   f. Click 'DOWNLOAD JSON' -> Rename the downloaded file to 'credentials.json'")
    print(f"   g. Move 'credentials.json' into this folder:")
    print(f"      {BASE_DIR}/credentials.json")
    print("\n5. Run this command once to authorize:")
    print("   python3 gdrive_sync.py auth")
    print("=" * 70 + "\n")


def get_gdrive_service():
    """Authenticates and returns the Google Drive API service instance."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"[!] Token refresh failed: {e}. Re-authenticating...")
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"\n[!] 'credentials.json' not found in workspace!")
                print_setup_guide()
                return None

            print("[*] Starting 1-time browser authorization for Google Drive...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
            print(f"[✓] Google Drive authorization saved to: {TOKEN_FILE}")

    service = build("drive", "v3", credentials=creds)
    return service


def get_or_create_folder(service, folder_name, parent_id=None):
    """Finds an existing folder or creates it if it does not exist."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    response = service.files().list(q=query, spaces="drive", fields="files(id, name, webViewLink)").execute()
    files = response.get("files", [])

    if files:
        return files[0]["id"], files[0].get("webViewLink")

    # Create the folder
    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    if parent_id:
        folder_metadata["parents"] = [parent_id]

    folder = service.files().create(body=folder_metadata, fields="id, webViewLink").execute()
    return folder.get("id"), folder.get("webViewLink")


def upload_or_update_file(service, local_path, folder_id, remote_name=None):
    """Uploads a local file or updates it if a file with the same name already exists."""
    if not os.path.exists(local_path):
        return None

    filename = remote_name or os.path.basename(local_path)
    mime_type, _ = mimetypes.guess_type(local_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)

    # Check if file already exists in folder
    query = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
    response = service.files().list(q=query, spaces="drive", fields="files(id, name, webViewLink)").execute()
    files = response.get("files", [])

    if files:
        file_id = files[0]["id"]
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media,
            fields="id, name, webViewLink"
        ).execute()
        return updated_file
    else:
        file_metadata = {
            "name": filename,
            "parents": [folder_id]
        }
        new_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink"
        ).execute()
        return new_file


def sync_to_google_drive(mode="all"):
    """
    Syncs the latest generated puzzle, trap, blunder, endgame, or solution
    to Google Drive inside 'PICT Knight Shift - WhatsApp Puzzles / Today's Challenge'.
    """
    service = get_gdrive_service()
    if not service:
        return False

    print(f"[*] Connecting to Google Drive...")
    root_id, root_link = get_or_create_folder(service, ROOT_FOLDER_NAME)
    today_id, today_link = get_or_create_folder(service, "Today's Challenge", parent_id=root_id)

    files_to_sync = []

    # Map candidate files based on what exists locally
    candidates = [
        ("chesscom_daily_puzzle.png", "1_Daily_Puzzle_Board.png"),
        ("whatsapp_puzzle_message.txt", "1_Daily_Puzzle_Caption.txt"),
        ("whatsapp_poll_options.txt", "1_Daily_Puzzle_Poll.txt"),
        ("chesscom_solution_animation.gif", "2_Solution_Animation.gif"),
        ("whatsapp_solution_message.txt", "2_Solution_Caption.txt"),
        ("chesscom_trap_board.png", "3_Opening_Trap_Board.png"),
        ("whatsapp_trap_message.txt", "3_Opening_Trap_Caption.txt"),
        ("whatsapp_trap_poll.txt", "3_Opening_Trap_Poll.txt"),
        ("whatsapp_trap_solution.txt", "3_Opening_Trap_Solution.txt"),
        ("chesscom_blunder_board.png", "4_Blunder_Board.png"),
        ("whatsapp_blunder_message.txt", "4_Blunder_Caption.txt"),
        ("whatsapp_blunder_poll.txt", "4_Blunder_Poll.txt"),
        ("whatsapp_blunder_solution.txt", "4_Blunder_Solution.txt"),
        ("chesscom_endgame_board.png", "5_Endgame_Board.png"),
        ("whatsapp_endgame_message.txt", "5_Endgame_Caption.txt"),
        ("whatsapp_endgame_poll.txt", "5_Endgame_Poll.txt"),
        ("whatsapp_endgame_solution.txt", "5_Endgame_Solution.txt"),
    ]

    synced_count = 0
    print(f"[*] Uploading files to Google Drive folder: '{ROOT_FOLDER_NAME} / Today\'s Challenge'...")
    for local_name, remote_name in candidates:
        local_path = os.path.join(BASE_DIR, local_name)
        if os.path.exists(local_path):
            res = upload_or_update_file(service, local_path, today_id, remote_name=remote_name)
            if res:
                print(f"  [✓] Uploaded: {remote_name}")
                synced_count += 1

    print("\n" + "=" * 65)
    print("  📱 GOOGLE DRIVE MOBILE SYNC COMPLETE")
    print("=" * 65)
    print(f"• Synced Files: {synced_count} file(s) updated")
    print(f"• Google Drive Folder: {ROOT_FOLDER_NAME} / Today's Challenge")
    if today_link:
        print(f"• Direct Web Link:     {today_link}")
    print("=" * 65)
    print("[*] On your mobile phone:")
    print("    1. Open the Google Drive app.")
    print("    2. Open 'PICT Knight Shift - WhatsApp Puzzles' -> 'Today's Challenge'.")
    print("    3. Save the image to your gallery and copy the caption text directly to WhatsApp!\n")
    return True


def upload_entire_curriculum(export_dir=None):
    """
    Recursively uploads the entire exported 1-Year Curriculum folder
    (Months 01-12 with all categories) to Google Drive.
    """
    if export_dir is None:
        if os.path.exists(os.path.join(BASE_DIR, "PICT Knight Shift Curriculum")):
            export_dir = os.path.join(BASE_DIR, "PICT Knight Shift Curriculum")
        else:
            export_dir = os.path.join(BASE_DIR, "exported_curriculum")

    if not os.path.exists(export_dir):
        print(f"[!] Export directory not found: {export_dir}")
        print("[*] Run 'python3 export_curriculum.py' first to generate all files!")
        return False

    service = get_gdrive_service()
    if not service:
        return False

    root_name = "PICT Knight Shift - 1-Year Curriculum"
    print(f"[*] Ensuring root folder '{root_name}' exists in Google Drive...")
    root_id, root_link = get_or_create_folder(service, root_name)

    total_uploaded = 0
    month_dirs = sorted([d for d in os.listdir(export_dir) if os.path.isdir(os.path.join(export_dir, d)) and not d.startswith(".")])

    for m_dir_name in month_dirs:
        m_local_path = os.path.join(export_dir, m_dir_name)
        print(f"\n[*] Syncing {m_dir_name}...")
        m_gdrive_id, _ = get_or_create_folder(service, m_dir_name, parent_id=root_id)

        cat_dirs = sorted([c for c in os.listdir(m_local_path) if os.path.isdir(os.path.join(m_local_path, c)) and not c.startswith(".")])
        for cat_name in cat_dirs:
            cat_local_path = os.path.join(m_local_path, cat_name)
            cat_gdrive_id, _ = get_or_create_folder(service, cat_name, parent_id=m_gdrive_id)

            files = sorted([f for f in os.listdir(cat_local_path) if not f.startswith(".")])
            for filename in files:
                f_path = os.path.join(cat_local_path, filename)
                res = upload_or_update_file(service, f_path, cat_gdrive_id, remote_name=filename)
                if res:
                    total_uploaded += 1
            print(f"  [✓] {cat_name}: {len(files)} files synced")

    print("\n" + "=" * 65)
    print("  🎉 COMPLETE 1-YEAR CURRICULUM UPLOADED TO GOOGLE DRIVE")
    print("=" * 65)
    print(f"• Total Files Uploaded: {total_uploaded}")
    print(f"• Root Folder:          {root_name}")
    if root_link:
        print(f"• Direct Link:          {root_link}")
    print("=" * 65)
    print("[*] On your mobile phone:")
    print("    Open Google Drive ➔ 'PICT Knight Shift - 1-Year Curriculum' ➔ Browse any month!\n")
    return True


def check_auth_status():
    """Prints the current Google Drive authentication status."""
    has_creds = os.path.exists(CREDENTIALS_FILE)
    has_token = os.path.exists(TOKEN_FILE)

    print("\n" + "=" * 55)
    print("  🔐 GOOGLE DRIVE AUTHENTICATION STATUS")
    print("=" * 55)
    print(f"• credentials.json: {'[✓] Present' if has_creds else '[✗] Missing'}")
    print(f"• token.json:       {'[✓] Authorized' if has_token else '[✗] Not authorized'}")
    print("=" * 55)

    if has_token:
        print("Google Drive is fully authorized and ready to sync!")
    elif has_creds:
        print("credentials.json is present. Run 'python3 gdrive_sync.py auth' to log in.")
    else:
        print_setup_guide()


def main():
    args = sys.argv[1:]
    cmd = args[0].lower() if args else "sync"

    if cmd in ["status", "check"]:
        check_auth_status()
    elif cmd in ["guide", "help", "setup"]:
        print_setup_guide()
    elif cmd in ["auth", "login"]:
        service = get_gdrive_service()
        if service:
            print("[✓] Successfully authenticated with Google Drive!")
    elif cmd in ["all", "upload-all", "batch"]:
        upload_entire_curriculum()
    elif cmd in ["sync", "upload", "push"]:
        sync_to_google_drive()
    else:
        print(f"Usage: python3 gdrive_sync.py [sync|all|auth|status|guide]")


if __name__ == "__main__":
    main()
