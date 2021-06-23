# Google Form/Drive Assignment Submission System #

First developed by A/Prof. Sebastian Sardina and Marco Tamassia for RMIT University COSC1125/1127 Artificial Intelligence 2017.

Contact: ssardina@gmail.com

## Description

This Python system handles assignment submissions stored in Google Drive, for example via Google Forms. 
When the submissions are in Google Drive, the script is able to retrieve their latest version per student automatically.

There are 2 mains scripts:

- `download_submissions.py`: download the latest submissions from Google Drive and set the student number and timestamp as file name. Currently they are downloaded as `.zip` files.
- `files2dir.py`: expand (for zip files) or copy (regular) files into directories per student.

The zip files or student folders can then be used for automarking, plagiarism detection (e.g., using MOSS), etc.

### Requirements

Works with Python 3. Install dependencies by executing:

```shell
pip install -r requirements.txt
```

## Prepare Google Forms for submissions

Basically, you need a way to store submissions in Google Drive. This can be done by either:

- A Google From with upload capabilities.
  - An RMIT template example can seen here: http://tinyurl.com/m2ply3l
  - Send me an email if you want a copy of that form.
- Use the following Google Scripts system to enhance a form to upload files to Google Drive:
  - https://www.labnol.org/internet/receive-files-in-google-drive/19697/
  - https://www.labnol.org/internet/file-upload-google-forms/29170/

Remember to set it to collect University email addresses IDs or Gmail address.  Otherwise, there is no way to confidently associate a submission with an id.

One field in the submission that I use handles HONOR CODE, taken from Khan Academy:

```
"I certify that this is all my own original work. If I took any parts from elsewhere, then they were non-essential parts of the project, and they are clearly attributed at the top of the file and in a separate report.  I will show I agree to this honor code by typing "Yes":
This declaration is the same as the one in Khan Academy.  We trust you all to submit your own work only; please don't let us down. If you do, we will pursue the strongest consequences available to us. You are always better off getting a very bad mark (even zero) than risking to go that path, as the consequences are serious for students. The project will not be marked unless this question is answered correctly and exactly with "Yes" as required. "
```

## Bulk download of submissions

The best way to get all the files from a Google Drive folder is to use the folder ID that can be obtained from the URL; for example:

```shell
python3 download_submissions.py --gdrive-id 0B7Whncx6ucnBfjZmOXZOZTJ5M0NLZjVzeVlGUW01N2JONHpDT2JSUmtpNzA0bFdBWmhFbVU \
    --submissions-dir submissions-zip/ -submission-extension pdf
```

The script will look for `credentials.txt` file to authenticate to GDrive. If there is none, it will open a browser session and ask you to authenticate. It will then store the credential in the file for further use. 

If the authentication is failing, delete `credentials.txt` and re-authenticate again.

It is possible to specify the whole folder dir instead of the folder id, but this is much more error-prone; for example:

```shell
python3 download_submissions.py --gdrive-path Courses/AI/2017/ass/Your\ submission\ package\ \(File\ responses\) \
        --submissions-dir submissions-zip/
```

By default, skipped submissions that already exist are not reported, use `--report-skip` for that.

## Expand files into folders

Once all files have been downloaded, we can generate one folder per student and either copy or  unpack (if a zip file) into the folder follows:

```shell
$ python3 files2dirs.py --sub-dir submissions-zip/ --output-dir student-dirs/
```

**WARNING:** Unfortunately, Python unzip fails with some cases that have the wrong magic number, but they do work using unzip. Also, if the zip file has folders, they will be re-created and the automarker won't find the files. To get around both issues, I prefer to use the following shell command:

```shell
for i in s*.zip; do unzip -j -o "$i" -d `sed "s/_.*//" <<< $i` ; done
```

This will create on directory per student and unpack all without re-creating the zip structure. So, if a student included the files in folders, they will be flatten out.

If the submission files are not the default `.zip` files, then we can use the `--ext` option to gather the right files:

```shell
$ python3 files2dirs.py --sub-dir submissions/ --output-dir student-dirs/ --ext cnf
```

This will copy each `.cnf` file in `submissions/` into a student folder within `student-dirs/`.

If you want to move all resulting directories somewhere else:

```shell
find . -maxdepth 1 -type d -exec mv {} ../sub-01/ \;
```

## Move files to student number folders via scripting

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

## Other info & scripts

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