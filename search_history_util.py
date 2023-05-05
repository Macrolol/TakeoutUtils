import argparse
import configparser
import os
import re
import zipfile

drive = False
try:
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive
    from google.colab import auth
    from oauth2client.client import GoogleCredentials
    drive = True
except ImportError:
    print("pydrive, google.colab, or oauth2client not installed. Run the following command to install them:")
    print("pip install pydrive google-colab oauth2client")
    print("Continuing without Google Drive support...")

from lxml import etree
import lxml.html
import pandas as pd


def extract_zip(zip_path, dest):
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest)

def extract_from_google_drive(file_name, dest):
    if not drive:
        print("Google Drive support not available")
        print("To enable drive support lease use 'pip install pydrive google-colab oauth2client' to install the necessary libraries")

        return
    auth.authenticate_user()
    gauth = GoogleAuth()
    gauth.credentials = GoogleCredentials.get_application_default()
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile({'q': f"title='{file_name}'"}).GetList()
    if len(file_list) == 0:
        print(f"No file named {file_name} found in Google Drive")
        return

    file_id = file_list[0]['id']
    downloaded = drive.CreateFile({'id': file_id})
    downloaded.GetContentFile('temp.zip')

    if zipfile.is_zipfile('temp.zip'):
        extract_zip('temp.zip', dest)
    else:
        print(f"{file_name} is not a zip file")

    os.remove('temp.zip')

def extract_sections(html):
    parsed = lxml.html.fromstring(html)
    outer_cells = parsed.cssselect(".outer-cell.mdl-cell.mdl-cell--12-col.mdl-shadow--2dp")
    return outer_cells

def list_searches(data_file, output_format, search_type, limit_option, limit_value):
    with open(data_file) as f:
        html = f.read()
    sections = extract_sections(html)
    data = []
    bad_entries = []
    timestamp_pattern = r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b \d{1,2}, \d{4}, \d{1,2}:\d{2}:\d{2}(?:&#8239;)?(?:AM|PM) (?:EDT|EST|CDT|CST|MDT|MST|PDT|PST))"
    for ele in sections:
        section_info = {
            'heading': ele.find_class('mdl-typography--title')[0].text_content(),
        }

        content = ele.find_class('content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1')[0]
        content_text  = content.text_content()
        section_info['action'] = content_text.partition('\xa0')[0]
        section_info['timestamp'] = re.search(timestamp_pattern, etree.tostring(content).decode('utf8')).group(1).replace('&#8239;', '')

        try:
            a_tag = content.cssselect('a')[0]
            section_info['url'] = a_tag.get('href')

            caption = ele.cssselect('div.content-cell.mdl-cell.mdl-cell--12-col.mdl-typography--caption > a')
            if len(caption) > 1:
                section_info['location'] = caption[0].get('href')

            if section_info['action'].startswith('Searched for'):
                section_info['search_query'] = a_tag.text_content()
            else:
                section_info['site_title'] = a_tag.text_content()

        except IndexError:
            bad_entries.append(ele)

        data.append(section_info)
    
    if not data:
        print("No data found")
        return
    else:
        print(f"Found {len(data)} entries")

    if search_type == "searches_only":
        filtered_data = [d for d in data if 'search_query' in d]
    elif search_type == "visited_only":
        filtered_data = [d for d in data if 'site_title' in d]
    else:
        filtered_data = data

    if limit_option == "head":
        filtered_data = filtered_data[:limit_value]
    elif limit_option == "tail":
        filtered_data = filtered_data[-limit_value:]
    elif limit_option == "every":
        filtered_data = filtered_data[::limit_value]

    df = pd.DataFrame(filtered_data)

    if output_format == "json":
        print(df.to_json(orient="records", lines=True))
    elif output_format == "csv":
        print(df.to_csv(index=False))
    else:
        print('Invalid output format')



def main():
    parser = argparse.ArgumentParser(description="A utility for Google Drive and Google activity",
                                     usage="%(prog)s [subcommand] --help for subcommand help")

    subparsers = parser.add_subparsers(dest="command", title="subcommands",
                                       description="Use script [subcommand] --help for usage info for the subcommands")

    # --unzip-from-drive sub-command
    unzip_parser = subparsers.add_parser("unzip-from-drive", help="Copy and extract a file from Google Drive to the local machine")
    unzip_parser.add_argument("source", help="Source path in Google Drive")
    unzip_parser.add_argument("target", help="Target path on the local machine")

    # --list-searches sub-command
    list_parser = subparsers.add_parser("list-searches", help="List user activities from '/My Activity/Search/MyActivity.html'")
    list_parser.add_argument("path", help="Path to 'MyActivity.html' file")

    # Output format
    list_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format: json or csv")

    # Output information
    info_group = list_parser.add_mutually_exclusive_group(required=True)
    info_group.add_argument("--all", action="store_true", help="Output all activities")
    info_group.add_argument("--searches_only", action="store_true", help="Output searches only")
    info_group.add_argument("--visited_only", action="store_true", help="Output visited pages only")

    # Number of entries options
    entries_group = list_parser.add_mutually_exclusive_group()
    entries_group.add_argument("--head", type=int, help="Output the latest N entries")
    entries_group.add_argument("--tail", type=int, help="Output the oldest N entries")
    entries_group.add_argument("--every", type=int, help="Output every N entries")

    args = parser.parse_args()

    if args.command == "unzip-from-drive":
        extract_from_google_drive(args.source, args.target)
    elif args.command == "list-searches":
        search_type = "all"
        if args.searches_only:
            search_type = "searches_only"
        elif args.visited_only:
            search_type = "visited_only"

        limit_option = None
        limit_value = None
        if args.head:
            limit_option = "head"
            limit_value = args.head
        elif args.tail:
            limit_option = "tail"
            limit_value = args.tail
        elif args.every:
            limit_option = "every"
            limit_value = args.every

        list_searches(args.path, args.format, search_type, limit_option, limit_value)
    else:
        print(f"Invalid command: {args.command}")

if __name__ == "__main__":
    main()