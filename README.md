# aix

Some useful AIX scripts<br/>

"errpt -a" to json converter:<br/>
Script is using "pyparsing" module brought by Paul McGuire (https://pyparsing-docs.readthedocs.io/en/latest/).<br/>
It converts "errpt -a" output to json, which may easily be used for storing, searching etc.<br/>

Usage:<br/>
- Piping standard input <br/>
errpt -a | python errpt-a_to_json.py<br/>
- Via a source file or directory<br/>
python errpt-a_to_json.py -s "*.raw"<br/>
python errpt-a_to_json.py -s "/tmp/2023[0-9]*"<br/>
- Via a destination file or directory<br/>
python errpt-a_to_json.py -s "*.raw" -d "./test/"<br/>
python errpt-a_to_json.py -s "/tmp/2023[0-9]*" -d "./errpt.json"<br/>
- Parsed raw files can be removed by "-r" option.<br/>
python errpt-a_to_json.py -s . -r<br/>
python errpt-a_to_json.py -s /tmp -r<br/>
