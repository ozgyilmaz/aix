# aix

Some useful AIX scripts<br/>

"errpt -a" to json converter:<br/>
Script is using "pyparsing" module brought by Paul McGuire (https://pyparsing-docs.readthedocs.io/en/latest/).<br/>
It converts "errpt -a" output to json, which may easily be used for storing, searching etc.<br/>

Usage:<br/>
- Piping standard input <br/>
errpt -a | python errpt-a_to_json.py<br/>
- Via a work directory. So the script will find all files with "raw" extension in the given directory and it's subdirectories.<br/>
python errpt-a_to_json.py -w .<br/>
python errpt-a_to_json.py -w /tmp<br/>
- Parsed raw files can be removed by "-r" option.<br/>
python errpt-a_to_json.py -w . -r<br/>
python errpt-a_to_json.py -w /tmp -r<br/>
