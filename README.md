First developed by Sebastian Sardina and Marco Tamassia for COSC1125/1127 Artificial Intelligence 2017.

Contact: ssardina@gmail.com


This is a system to handle assignment submissions via Google Forms. There are 2 mains scripts:

- download_submissions.py: 
    download the latests submissions from Google Drive and set the student number as file name
- expand_zip_files.py:
    expands zip files into directories per student



The zip files or directories can then be used for automarking, plagarism detection (e.g., using MOSS), etc.


===============================
CREATE GOOGLE FORMS FOR SUBMISSIONS
===============================

- Create a Google Form to accept submissions.
    - An RMIT template example can seen here: http://tinyurl.com/m2ply3l
    - Send me an email if you want a copy of that form.

    - It has to be with a coorporative Google system to be able to add an Upload file field.
    Forms done with a standard Google account does not allow you to add upload files.    
    
- Remember to set it to collect University email addresses IDs or Gmail address. Oherwise there is no way to confidently associate a submission with an id.

- One field in the submission that I use handles Honor Code, taken from Khan Academy:

    I certify that this is all my own original work. If I took any parts from elsewhere, then they were non-essential parts of the project, and they are clearly attributed at the top of the file and in a separate report.  I will show I agree to this honor code by typing "Yes":

    This declaration is the same as the one in Khan Academy.  We trust you all to submit your own work only; please don't let us down. If you do, we will pursue the strongest consequences available to us. You are always better off getting a very bad mark (even zero) than risking to go that path, as the consequences are serious for students. The project will not be marked unless this question is answered correctly and exactly with "Yes" as required. 



===============================
DOWNLOAD ALL LATEST SUBMISSIONS DIRECTORY
===============================

Get all the submission files (the script will handle multiple submissions and keep the latest always):


    python download_submissions.py --gdrive-path Courses/Artificial\ Intelligence/2017/assessments/submissions/AI17\ Submission\ -\ Project\ 1\:\ Search\ in\ Pacman\ \(File\ responses\)/Your\ submission\ package\ \(File\ responses\) --submissions-dir submissions-zip/


OR using the Google Folder ID:


    python download_submissions.py --gdrive-id 0B7Whncx6ucnBfjZmOXZOZTJ5M0NLZjVzeVlGUW01N2JONHpDT2JSUmtpNzA0bFdBWmhFbVU --submissions-dir submissions-zip/



===============================
PRODUCE DIRECTORIES
===============================


This will produce one directory per student and unpack the zip there:

    python expand_zip_files.py --zip-dir submissions-zip/ --output-dir submissions-dir/