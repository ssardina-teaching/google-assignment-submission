# Google Form/Drive Assignment Submission System

## REPO HAS BEEN ARCHIVED AND SCRIPTS MOVED TO THIS REPO: https://github.com/ssardina-teaching/git-hw-submissions

This Python tools allows to download and manipulates files in Google Drive. Those files may have been submitted by students via Google Forms.

It was first developed by A/Prof. Sebastian Sardina and Marco Tamassia for RMIT University COSC1125/1127 Artificial Intelligence 2017, and subsequently extended/improved to cater for my courses.

There are 2 mains scripts:

- `download_submissions.py`: download the latest submissions from Google Drive and set the student number and timestamp as file name. Currently they are downloaded as `.zip` files.
- `files2dir.py`: expand (for zip files) or copy (regular) files into directories per student.

The zip files or student folders can then be used for automarking, plagiarism detection (e.g., using MOSS), etc.

- [Google Form/Drive Assignment Submission System](#google-formdrive-assignment-submission-system)
  - [Requirements \& Authentication](#requirements--authentication)
    - [Google API Python Client](#google-api-python-client)
  - [Bulk drive download via PyDrive](#bulk-drive-download-via-pydrive)
  - [Fill Google Forms with marking](#fill-google-forms-with-marking)
  - [Other useful tools](#other-useful-tools)
    - [Expand files into folders](#expand-files-into-folders)
    - [Move files to student number folders via scripting](#move-files-to-student-number-folders-via-scripting)
    - [Errors in unzipping submissions](#errors-in-unzipping-submissions)
    - [Keeping submissions in a list of student numbers](#keeping-submissions-in-a-list-of-student-numbers)
    - [Rename all files within student folders](#rename-all-files-within-student-folders)

## Requirements & Authentication

The system uses [PyDrive](https://pythonhosted.org/PyDrive/), a wrapper on top of [google-api-python-client](https://github.com/googleapis/google-api-python-client/) to simplify access to the Google Drive (via the API).

**Note**: as of 2021, PyDrive is archived and replaced with [PyDrive2](https://github.com/iterative/PyDrive2). The `download_submissions.py` script here is still in PyDrive as of July, 2023 and needs to be migrated.

```shell
$ pip install pydrive pytz iso8601 pandas
```

Or just install al via:  `pip install -r requirements.txt`

### Google API Python Client

The [google-api-python-client](https://github.com/googleapis/google-api-python-client/) is the main client which has access to all the API provided. 
  - Note: they recommend moving towards the [Google Cloud Python Client](https://github.com/googleapis/google-cloud-python).

In July 2023, I tried to use this for editing and marking quizzes in Google Form, but the client is still too low-level and doesn't provide classes for Google Drive or Google Forms for example. I couldn't find a Google Form wrapper as there is for the drive.

To install these packages:

``` shell
$ pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
$ pip instal oauth2client
```

All access to Google API requires authentication; usually the workflow is as follows:

1. Go to the [Google API Access Panel](https://console.developers.google.com/apis/credentials).
2. Create a project.
3. Create an OAuth consent screen.
4. Create credentials of type "OAuth Client ID".
5. Download the JSON file of such credentials and name it `client_secrets.json`
6. Place the file in the same directory as the scripts.

## Bulk drive download via PyDrive

The script relies on [PyDrive](https://pythonhosted.org/PyDrive/), which access Google services via an API. To access the API you need to authenticate and ultimately have a proper `credentials.txt` file from where you execute the script. But first you need to generate a `client_secret.json` file. Please follow the [PyDrive Authentication instructions](https://pythonhosted.org/PyDrive/quickstart.html#authentication).

The best way to get all the files from a Google Drive folder is to use the folder ID that can be obtained from the URL; for example:

```shell
$ python download_submissions.py --gdrive-id 0B7Whncx6ucnBfjZmOXZOZTJ5M0NLZjVzeVlGUW01N2JONHpDT2JSUmtpNzA0bFdBWmhFbVU \
    --submissions-dir submissions-zip/ -submission-extension pdf
```

**Note:** The script will look for `credentials.txt` file to authenticate to GDrive. If there is none, but a `client_secrets.json` is available (see above), it will open a browser session and ask you to authenticate. It will then store the credential in the file for further use. If the authentication is failing, delete `credentials.txt` and re-authenticate again.

It is possible to specify the whole folder dir instead of the folder id, but this is much more error-prone; for example:

```shell
$ python download_submissions.py --gdrive-path Courses/AI/2017/ass/Your\ submission\ package\ \(File\ responses\) \
        --submissions-dir submissions-zip/
```

By default, skipped submissions that already exist are not reported, use `--report-skip` for that.

## Fill Google Forms with marking

We want to fill forms using the Google API. A possibility would be to use a Bot using Salenium, like [this one](https://github.com/skyrunner360/ADYPU_Feedback_form_filling_Bot).

We tried to get a system using the [Google Forms API](https://developers.google.com/forms/api/guides)  via the Python client, but it is way too low-level. I couldn't find any high-level interface for Google Forms as `PyDrive` is for the Google Drive.

At this point the best solution is to keep [editing forms via the App Script inside the Google Sheet](https://developers.google.com/apps-script/reference/forms/quiz-feedback-builder).


------------------------
## Other useful tools
### Expand files into folders

Once all files have been downloaded, we can generate one folder per student and either copy or  unpack (if a zip file) into the folder follows:

```shell
$ python files2dirs.py submissions-zip/ student-dirs/
```

**WARNING:** Unfortunately, Python unzip fails with some cases that have the wrong magic number, but they do work using unzip. Also, if the zip file has folders, they will be re-created and the automarker won't find the files. To get around both issues, I prefer to use the following shell command:

```shell
$ for i in s*.zip; do unzip -j -o "$i" -d `sed "s/_.*//" <<< $i` ; done
```

This will create on directory per student and unpack all without re-creating the zip structure. So, if a student included the files in folders, they will be flatten out.

If the submission files are not the default `.zip` files, then we can use the `--ext` option to gather the right files:

```shell
$ python files2dirs.py --ext cnf submissions/ student-dirs/
```

This will copy each `.cnf` file in `submissions/` into a student folder within `student-dirs/`. Use the `rename` tool to do more renaming of files as necessary.

If you want to move all resulting directories somewhere else:

```shell
$ find . -maxdepth 1 -type d -exec mv {} ../sub-01/ \;
```

### Move files to student number folders via scripting

We can create folders and move the files via shell scripting too. Suppose submissions are meant to be `.cnf` file (not `.zip` as produced by the download script).

First rename the files to the correct extension:

```shell
$ rename 's/\.zip/\.cnf/' *.zip
```

Next, many marking systems will require each student in its own folder with the student number. The student number is in the download file in the first 9 letters, so this will do it:

```shell
$ for f in *.cnf ; do mkdir ${f:0:8}; mv $f ${f:0:8}  ; done
```

After that, each student submission will be placed in a folder `sXXXXXXX/`.

### Errors in unzipping submissions

For some submissions, you may see errors as follows:

```shell
Wed, 21 Aug 2019 20:24:18 ERROR    Cannot expand file s3627828_2019-08-18T20:35:03.949000+10:00.zip: <class 'zipfile.BadZipFile'> (Bad magic number for file header)
```

### Keeping submissions in a list of student numbers

Suppose you get all submissions but you don't want to process them all, for example because some correspond to students who have dropped the course.

First, generate a text file, say `list-enrolled.txt` with all the student numbers that are still enrolled; for example:

```
$ cat list-enrolled.txt
6842580
8781445
9750989
1682429
2792522
...
```

Next, if all submissions are in `sub/`, move all submissions to a folder called `submissions-enrolled/` as follows:

```shell
cat list.txt | while read STUDENT; do find sub/  -type f \
    -name "s${STUDENT}*" -exec mv {} submissions-enrolled/ \; ;done
```

Remember that a submission has this form:

```
s1234572_2020-04-29T11:57:28.682000+10:00.pdf
```

### Rename all files within student folders

Suppose every student has a folder `sXXXXXX` and inside his/her file. To rename all to the same name, say, `sea-domain.cnf`:

```shell
$ rename 's/(.*)\/.*/$1\/sea-domain.cnf/' */*.cnf
```
