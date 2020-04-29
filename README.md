# Google Form/Drive Assignment Submission System #

First developed by A/Prof. Sebastian Sardina and Marco Tamassia for RMIT University COSC1125/1127 Artificial Intelligence 2017.

Contact: ssardina@gmail.com

## Description

This Python system handles assignment submissions stored in Google Drive, for example via Google Forms. 
When the submissions are in Google Drive, the script is able to retrieve their latest version per student automatically.

There are 2 mains scripts:

- `download_submissions.py`: 
    download the latest submissions from Google Drive and set the student number and timestamp as file name
- `expand_zip_files.py`:
    expands zip files into directories per student


The zip files or directories can then be used for automarking, plagarism detection (e.g., using MOSS), etc.

### Requirements

Works with Python 3. Install dependencies by executing:

```
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
This declaration is the same as the one in Khan Academy.  We trust you all to submit your own work only; please don't let us down. If you do, we will pursue the strongest consequences available to us. You are always better off getting a very bad mark (even zero) than 
risking to go that path, as the consequences are serious for students. The project will not be marked unless this question is answered correctly and exactly with "Yes" as required. "
```

## Running the script

- Download all latest submissions directory by using the path in Google Drive by specifying the folder from the user root folder:
    
```
python3 download_submissions.py --gdrive-path Courses/Artificial\ Intelligence/2017/assessments/submissions/AI17\ Submission\ \
        -\ Project\ 1\:\ Search\ in\ Pacman\ \(File\ responses\)/Your\ submission\ package\ \(File\ responses\) \
        --submissions-dir submissions-zip/
```
       
- Same but using the Google Folder ID (easier, less error-prone):

```
python3 download_submissions.py --gdrive-id 0B7Whncx6ucnBfjZmOXZOZTJ5M0NLZjVzeVlGUW01N2JONHpDT2JSUmtpNzA0bFdBWmhFbVU \
    --submissions-dir submissions-zip/
```
  
- By default, skipped submissions that already exist are not reported, use `--report-skip` for that.

The first time, the browser will open to authorize the execution of the script. Make sure you log into the RMIT account. After that, a `credentials.txt` file will be saved that will be used next time for authentication.

## Building dirs from zip files
    
Once all .zip files have been downloaded, we can generate one directory per student and unpack the zip into it follows:

```
python3 expand_zip_files.py --zip-dir submissions-zip/ --output-dir submissions-dir/
```

Unfortunately, Python unzip fails with some cases that have the wrong magic number, but they do work using unzip. Also, if the zip file has folders, they will be re-created and the automarker won't find the files.

So, to get around both issues, I prefer to use the following shell command:

    for i in s*.zip; do unzip -j -o "$i" -d `sed "s/_.*//" <<< $i` ; done
    
This will create on directory per student and unpack all without re-creating the zip structure. So, if a student included the files in folders, they will be flatten out.

If you want to move all resulting directories somewhere else:

    find . -maxdepth 1 -type d -exec mv {} ../sub-01/ \;



## Errors in unzipping submissions

For some submissions, you may see errors as follows:

Wed, 21 Aug 2019 20:24:18 ERROR    Cannot expand file s3627828_2019-08-18T20:35:03.949000+10:00.zip: <class 'zipfile.BadZipFile'> (Bad magic number for file header)


