"""
To change credentials:
- Go to the Google API Access Pane (https://console.developers.google.com/apis/credentials)
- Create a project
- Create an OAuth consent screen
- Create credentials of type "OAuth Client ID"
- Download the JSON file of such credentials and name it "client_secrets.json"
- Place the file in the same directory as this file

"""
import os
import re
import sys
import argparse
from collections import defaultdict, namedtuple
from pytz import timezone
import glob
import logging


try:
    import iso8601
except:
    print('Iso8601 is not installed. Please, run `pip install iso8601`')
    sys.exit(1)

try:
    import pandas as pd
except:
    print('Pandas is not installed. Please, run `pip install pandas`')
    sys.exit(1)

try:
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive
except:
    print('PyDrive is not installed. Please, run `pip install pydrive`')
    sys.exit(1)


def get_path_pieces_reversed(path):
    """
    Breaks a given path into a list (of str) of components in reversed order.
    :param path: The path to be broken
    :return: The pieces of the path in reverse order
    """
    pieces_reversed = []
    cur_path, cur_file = path, None
    while cur_path != '':
        cur_path, cur_file = os.path.split(cur_path)
        pieces_reversed.append(cur_file)
    return pieces_reversed


def get_children_by_id(parent_id):
    """
    Gets a list of Google Drive files that are children of the parent with the given id.
    :param parent_id: The id of the parent directory
    :return:a list of Google Drive files that are children of the parent with the given id
    """
    return drive.ListFile({'q': "'%s' in parents and trashed=false" % parent_id}).GetList()


def get_id_by_absolute_path(path):
    """
    Given a path as a string, retrieves the id of the innermost component.
    :param path: The path to be analysed
    :return: The id of the innermost component
    """
    pieces_reversed = get_path_pieces_reversed(path)

    cur_list = get_children_by_id('root')
    final_id = None
    while pieces_reversed:
        target = pieces_reversed.pop()
        found = False
        for f in cur_list:
            if f['title'] == target:
                found = True
                if not pieces_reversed:
                    final_id = f['id']
                else:
                    if f['mimeType'] == 'application/vnd.google-apps.folder':
                        cur_list = get_children_by_id(f['id'])
                        break
                    else:
                        raise Exception("File encountered where a directory was expected: %s" % target)
        if not found:
            raise Exception('Directory not found: %s' % target)
    return final_id


def download_all_submissions(destination, submission_folder_id, overwrite):
    #  some initial useful definitions (to be used later)
    email_pattern = re.compile(r'(.+)@(?:student\.)?rmit\.edu\.(?:au|vn)')
    filename_pattern = re.compile(r'(.+)_(.+).zip')
    melbourne = timezone('Australia/Melbourne')
    submission_entry = namedtuple('submission_entry', ['timestamp', 'gdrive_id'])

    # if the destination directory does not exist, then create it
    if not os.path.exists(destination):
        os.makedirs(destination)

    # iterate thought all submitted files in the gdrive and extract the latest submission for each student
    # submission_folder_id = get_id_by_absolute_path(full_path)
    files_in_submission_folder = get_children_by_id(submission_folder_id) # list of files in submission folder
    unique_submissions = defaultdict(submission_entry) # we will build a collection of the latest student submissions here
    for f in files_in_submission_folder: # iterate through all the submitted files
        # get email and timestamp from google drive data
        email = f['lastModifyingUser']['emailAddress']
        submission_timestamp = iso8601.parse_date(f['createdDate']).astimezone(melbourne)
        # convert timestamp to melbourne time zone
        # see: http://www.saltycrane.com/blog/2009/05/converting-time-zones-datetime-objects-python/

        match = re.match(email_pattern, email)
        if match:
            student_id = match.group(1)
            # add/replace to unique collection if new student or older than before
            if student_id not in unique_submissions or unique_submissions[student_id].timestamp < submission_timestamp:
                unique_submissions[student_id] = submission_entry(timestamp=submission_timestamp, gdrive_id=f['id'])
        else:
            print('Very strange '+email+' is not a a valid email id. Skipping submission...')


    # Next, we download everything in unique_submissions form Gdrive
    for i, student_id in enumerate(unique_submissions):
        # get submission id and time
        latest_submission_timestamp, gdrive_id = unique_submissions[student_id]

        # check for existing  older submission files from the same student and remove them if any
        # submission time is included in the file name
        for existing_file in glob.glob(os.path.join(destination, '%s_*.zip' % student_id)):
            match = re.match(filename_pattern, existing_file)
            if match:
                try:
                    existing_submission_timestamp = iso8601.parse_date(match.group(2))
                    if existing_submission_timestamp < latest_submission_timestamp:
                        print('Removing outdated submission for %s' % student_id)
                        os.remove(existing_file)
                except:
                    print('[WARNING] Cannot parse date of file %s' % existing_file)

        # define name of output target file (include student number id + timestamp of file obtained)
        destination_file_path = os.path.join(destination, '%s_%s.zip' % (student_id, latest_submission_timestamp.isoformat()))
        # download it if not there or needs to be overwritten
        if not os.path.exists(destination_file_path) or overwrite:
            gdrive_file = drive.CreateFile({'id': unique_submissions[student_id].gdrive_id})
            if gdrive_file['title'].endswith('.zip'):
                print("Downloading submission for %s (%d/%d) - https://drive.google.com/open?id=%s" % (student_id, i+1, len(unique_submissions), unique_submissions[student_id].gdrive_id))
                gdrive_file.GetContentFile(destination_file_path)
            else:
                print("Submission by %s is not a .zip file - https://drive.google.com/open?id=%s" % (student_id, unique_submissions[student_id].gdrive_id))
        else:
            print("Skipping submission for %s (%d/%d) - submission in folder already (use --overwrite option to replace)" % (student_id, i+1, len(unique_submissions)))




if __name__ == '__main__':


    parser = argparse.ArgumentParser(
        description='This script downloads all submission zip files in a directory in Google Drive.\n'
                    'Notice that authentication on Google is required: the user will interactively\n'
                    'be prompted to login. Credentials will be saved in the file "credentials.json".\n'
                    '\n\n'
                    "Example usage: python download_submissions.py --gdrive-path 'assessments/submissions/AI17 Submission - Project 0: Python Warmup (File responses)/Your submission package (File responses)' --csv-path 'p0-responses.csv'",
        formatter_class = argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--gdrive-id',
        type=str,
        required=False,
        help='The folder in Google Drive where all submissions are located.'
    )
    parser.add_argument(
        '--gdrive-path',
        type=str,
        required=False,
        help='The full path of the directory containing all the zip files in Google Drive.'
    )
    parser.add_argument(
        '--reset-credentials',
        action='store_true',
        help='If given, existing credentials will be deleted.'
    )
    parser.add_argument(
        '--submissions-dir',
        type=str,
        default='submissions',
        help='Directory where the submissions should be downloaded.'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='If given, existing downloaded submissions will be overwritten. If not, they will be skipped.'
    )

    args = parser.parse_args()

    if args.gdrive_id is None and args.gdrive_path is None:
        logging.error("at least one of --gdrive-id --gdrive-path required")
        sys,exit(1)

    if args.reset_credentials and os.path.exists('credentials.json'):
        os.remove('credentials.json')

    gauth = GoogleAuth()
    gauth.LocalWebserverAuth() # Creates local web-server and auto handles authentication.

    drive = GoogleDrive(gauth) # Create GoogleDrive instance with authenticated GoogleAuth instance

    if not args.gdrive_path is None and args.gdrive_path.endswith('/'):
        args.gdrive_path = args.gdrive_path[:-1]

    if not args.gdrive_id is None:
        gdrive_id = args.gdrive_id
    else:
        gdrive_id = get_id_by_absolute_path(args.gdrive_path)

    download_all_submissions(args.submissions_dir, gdrive_id, args.overwrite)
