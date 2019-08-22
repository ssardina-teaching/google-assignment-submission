import argparse
import os
import sys
import zipfile
import re
import logging


# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')


"""
This script takes a list of zip files submitted (sXXXXXX_2017-03-25T10:35:06.132000+11:00) and unzips its content into XXXXXX
"""


if __name__ == '__main__':
    filename_pattern = re.compile(r'(.+)_(.+).zip')

    parser = argparse.ArgumentParser(
        description='This script takes zip files and produces directories for each student number\n',
        # formatter_class = argparse.RawTextHelpFormatter
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--zip-dir',
        type=str,
        default='./',
        help='Directory where zip files are located.'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        required=False,
        default='./',
        help='Directory where student directories will be placed.'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        default=False,
        help='Overwrite destination if exists.'
    )
    args = parser.parse_args()

    if not os.path.exists(args.zip_dir) or not os.path.isdir(args.zip_dir):
        logging.error('Submissions zip directory not found or not a directory: %s.' % args.zip_dir)
        sys.exit(1)

    if not os.path.exists(args.output_dir) or not os.path.isdir(args.output_dir):
        logging.error('Submission output directory not found or not a directory: %s.' % args.output_dir)
        sys.exit(1)

    filenames = next(os.walk(args.zip_dir))[2]
    for f in filenames:
        try:
            match = re.match(filename_pattern, f)
            student_dir = match.group(1)
            full_f = os.path.join(args.zip_dir, f)
            full_student_dir = os.path.join(args.output_dir, student_dir)
            if not os.path.exists(full_student_dir) or args.overwrite:
                if not os.path.exists(full_student_dir):
                    os.mkdir(full_student_dir)
                student_zip_file = zipfile.ZipFile(full_f)
                try:
                    student_zip_file.extractall(full_student_dir)
                    logging.info('Submission %s expanded in %s ' % (f, full_student_dir))
                except Exception as e:
                    logging.error('Unable to expand file {}: {} ({})'.format(f, type(e), e))
                    os.rmdir(full_student_dir)

        except:
            logging.warning("File %s cannot be processed - does not match pattern - no dir created for it!" % f)



