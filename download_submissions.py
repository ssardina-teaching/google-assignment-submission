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
import iso8601
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


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

"""
Download latest submission files in Google Drive folder with id gdrive_id with submission extension sub_ext (e.g., zip) 
to directory dir_destination. 
    If overwrite is true just replace ANY local copy. 
    If report_skip is true, do not report submissions that are skipped (because they already exist).
"""
def download_all_submissions(dir_destination, gdrive_id, overwrite, report_skip, sub_ext, check_extension):
    #  some initial useful definitions (to be used later)
    email_pattern = re.compile(r'(.+)@(?:student\.)?rmit\.edu\.(?:au|vn)')
    filename_pattern = re.compile(r'(.+)_(.+).' + sub_ext)   # s3600563_2020-04-29T08:12:23.723000+10:00.xxx
    melbourne = timezone('Australia/Melbourne')
    submission_entry = namedtuple('submission_entry', ['timestamp', 'gdrive_id'])

    # if the destination directory does not exist, then create it
    if not os.path.exists(dir_destination):
        os.makedirs(dir_destination)

    # Iterate thought all submitted files in the GDrive and extract the latest submission for each student
    #   Store that into unique_submissions
    files_in_submission_folder = get_children_by_id(gdrive_id)
    unique_submissions = defaultdict(submission_entry)
    for f in files_in_submission_folder:
        email = f['lastModifyingUser']['emailAddress']  # get email and timestamp from google drive data
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
            print('Very strange ' + email + ' is not a a valid email id. Skipping submission...')

    print("Number of unique submissions identified (many may already exist in local dir): %d \n" % len(
        unique_submissions))
    # Each entry in unique_submissions is of the form:
    #     'sebastian.sardina': submission_entry(timestamp=datetime.datetime(2020, 4, 28, 11, 1, 31, 994000,
    #           tzinfo= < DstTzInfo 'Australia/Melbourne' AEST + 10: 00:00 STD >),
    #           gdrive_id = '1rVGNfMA3Ja-zdYCJnpZqaXNtGeHj6Ia4')})

    # Next, we download everything in unique_submissions form Gdrive
    for i, student_id in enumerate(unique_submissions): # i is 0,1,2,3... and student_id is "s3844647"
        # get submission timestamp and Google Drive id to the document
        latest_submission_timestamp, gdrive_id = unique_submissions[student_id]

        # check for existing older submission files from the same student and remove them if any
        # submission time is included in the file name
        for existing_file in glob.glob(os.path.join(dir_destination, '%s_*.%s' % (student_id, sub_ext))):
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
        destination_file_path = os.path.join(dir_destination, '%s_%s.%s' % (
            student_id, latest_submission_timestamp.isoformat(), sub_ext))
        # download it if not there or needs to be overwritten
        if not os.path.exists(destination_file_path) or overwrite:
            gdrive_file = drive.CreateFile({'id': unique_submissions[student_id].gdrive_id})
            if not check_extension or gdrive_file['title'].endswith('.' + sub_ext):
                print("Downloading submission for %s (%d/%d) - https://drive.google.com/open?id=%s" % (
                    student_id, i + 1, len(unique_submissions), unique_submissions[student_id].gdrive_id))
                gdrive_file.GetContentFile(destination_file_path)
            else:
                print("Submission by %s does not have %s extension - https://drive.google.com/open?id=%s" % (
                    student_id, sub_ext, unique_submissions[student_id].gdrive_id))
        elif report_skip:
            print("Skipping submission for {:s} ({:d}/{:d}) - submission in folder already (use --overwrite option to replace)".format(
                    student_id, i + 1, len(unique_submissions)))








if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='This script downloads all submission zip files in a directory in Google Drive.\n'
                    'Notice that authentication on Google is required: the user will interactively\n'
                    'be prompted to login. Credentials will be saved in the file "credentials.json".\n'
                    '\n\n'
                    "Example usage: python download_submissions.py --gdrive-path 'assessments/submissions/AI17 Submission - Project 0: Python Warmup (File responses)/Your submission package (File responses)' --csv-path 'p0-responses.csv'",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--gdrive-id',
        type=str,
        default=None,
        help='The folder in Google Drive where all submissions are located.'
    )
    parser.add_argument(
        '--gdrive-path',
        type=str,
        default=None,
        help='The full path of the directory containing all the zip files in Google Drive.'
    )
    parser.add_argument(
        '--reset-credentials',
        action='store_true',
        help='If given, existing credentials will be deleted.'
    )
    parser.add_argument(  # TODO: needs to complete this capability
        '--dir-credentials',
        default='./',
        help='Path directory where the credential file client_secrets.json is located (not working yet) (default: %(default)s).'
    )
    parser.add_argument(
        '--submissions-dir',
        type=str,
        default='./',
        help='Directory where the submissions should be downloaded (default: %(default)s).'
    )
    parser.add_argument(
        '--submission-extension',
        type=str,
        required=False,
        default='zip',
        help='Extension of submission to gather (e.g., zip or pdf); otherwise any (default: %(default)s).'
    )
    parser.add_argument(
        '--check-extension',
        action='store_true',
        help='If given, submissions will be checked for the correct extension and skipped if incorrect.'
    )
    parser.add_argument(
        '--report-skip',
        action='store_true',
        help='If given, skipped files will be reported too; otherwise will be ignored.'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='If given, existing downloaded submissions will be overwritten. If not, they will be skipped.'
    )


    args = vars(parser.parse_args())
    print(args)

    if args['gdrive_id'] is None and args['gdrive_path'] is None:
        logging.error("at least one of --gdrive-id --gdrive-path required")
        sys, exit(1)

    if args['reset_credentials'] and os.path.exists('credentials.json'):
        os.remove('credentials.json')

    # gauth = GoogleAuth()
    # gauth.LocalWebserverAuth()  # Creates local web-server and auto handles authentication.

    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.txt")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()  # Creates local web-server and auto handles authentication.
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("credentials.txt")

    drive = GoogleDrive(gauth)  # Create GoogleDrive instance with authenticated GoogleAuth instance

    if not args['gdrive_path'] is None and args['gdrive_path'].endswith('/'):
        args['gdrive_path'] = args['gdrive_path'][:-1]

    if args['gdrive_id'] is None:
        # An absolute GDrive path was given, get the GDrive ID
        gdrive_id = get_id_by_absolute_path(args['gdrive_path'])
    else:
        gdrive_id = args['gdrive_id']

    download_all_submissions(args['submissions_dir'], gdrive_id, args['overwrite'], args['report_skip'],
                             args['submission_extension'], args['check_extension'])
