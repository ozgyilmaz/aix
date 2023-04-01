from pyparsing import *
import os
import json
import argparse
import sys
import glob
import pathlib
from datetime import datetime

# Custom action to strip the values
def strip_value(tokens):
    return [token.strip() for token in tokens]

# regex for separators used for key/value pairs of VPD blocks
# i.e. Manufacturer................SOMEVENDOR
regex_dotted_line       = Suppress(Regex("\.{2,}"))
# new line
NL = LineEnd()
# read everything until a dashed line or until EOF
# Thanks to PaulMcG
# https://stackoverflow.com/questions/75782477/how-to-use-pyparsing-for-multilined-fields-that-has-two-different-types-of-endin
dashed_separator = (("-" * 75) + NL | StringEnd()).suppress()
# grammar for vpd keys
# they may also contain a single dot, like: "Device Specific.(Z0)"
vpd_key     = Combine(Word(alphanums + " ") + ('.' + Word(alphanums+"("+")")) * (0,1))
# grammar for vpd values
vpd_value   = Word(alphanums+".")
# grammar for vpd key/value pair
vpd_line    = Dict(Group(vpd_key + regex_dotted_line + vpd_value))
# vpd grammar definition. We need to find at least one key/value pair if we hit a "VPD:" keyword
vpd_grammar = OneOrMore(vpd_line)
# standard info key definition like LABEL, IDENTIFIER etc
info_key            = Combine(Word(alphanums+" "+"/") + Suppress(":"))
# value may have alphanumeric chars, space, some special chars etc
# value also may have the whole VPD information and that should be
# also parsed as key/value pairs
info_value          = rest_of_line.addParseAction(strip_value) + Optional(vpd_grammar)
# an info key/value pair contains a "key" and a "value"
info_line           = Dict( Group( info_key + info_value ) )
# description has a special format... it doesnt have semicolon, also it's not
# clear where it finishes. 
# "probable cause", "user causes" etc will be parsed in next version of script
# description (as a whole text containing sub titles like probable cause etc)
# may end with a dashed line, or with EOF.
info_description    = Combine(
    Suppress("Description" + NL)
    + ZeroOrMore(rest_of_line + NL, stop_on=dashed_separator)
).setResultsName('Description')

# info grammar sums of everything
info_grammar        = Group(Suppress(Optional(("-" * 75))) + OneOrMore(info_line) + info_description)

# final grammar consists of one or more info grammars which mean errpt records
grammar = OneOrMore(info_grammar).setResultsName("Errpt Records")

# parse raw "errpt -a" string
def parse_string(raw_string):
    try:
        result = grammar.parseString(raw_string, parseAll=True).as_dict()
    except Exception as e:
        print(e)
        exit(1)
    return result

def dump_json(json_string,file):
    try:
        with open(file, "w+") as f:
            json.dump(json_string, f, indent=4)
    except Exception as e:
        print(e)
        exit(1)
    return
###################################
# main definition                 #
###################################

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="Source directory", dest="source", required=False)
    parser.add_argument("-d", "--destination", help="Destination file for json", dest="destination", required=False)
    parser.add_argument('-r', "--remove", action='store_true', required=False)
    args = parser.parse_args()

    # if there is no args.source then the source is stdin
    if args.source:
        file_list = glob.glob(args.source, recursive=True)
        final_dict = []

        for file in file_list:
            print("Parsing: " + file)
            with open(file,"r") as f:
                result = parse_string(f.read())
            # remove the source file
            if args.remove:
                if os.path.exists(file):
                    os.remove(file)
            # no destination file or folder given
            # so seperate output file in the same folder of raw file
            if not args.destination:
                dump_json(result,os.path.splitext(file)[0]+".json")
            # destination folder is given
            # so seperate create output file in destination folder
            elif args.destination and os.path.isdir(args.destination):
                dump_json(result, os.path.join(args.destination,  os.path.splitext(pathlib.Path(file).name)[0] + ".json"))
            # destination file is given
            # so merge all output in destination file
            # do not repeat same errpt data, be unique
            elif args.destination:
                try:
                    with open(args.destination, "r") as f:
                        final_dict = json.load(f)["Errpt Records"]
                except:
                    pass
                final_dict = final_dict + result['Errpt Records']
                # Define a new list to store the unique dictionaries
                unique_data = []
                # Define a set to keep track of the dictionaries we've already seen
                seen = set()
                # Loop over each dictionary in the original list
                for d in final_dict:
                    # Extract the relevant keys
                    key = (d['LABEL'], d['Date/Time'], d['Node Id'], d['Description'])
                    # Check if we've already seen this key
                    if key not in seen:
                        # If not, add the dictionary to the new list and mark it as seen
                        unique_data.append(d)
                        seen.add(key)
                # Sort dictionaries according to date/time
                sorted_data = sorted(unique_data, key=lambda x: datetime.strptime(x['Date/Time'], '%a %b %d %H:%M:%S +03 %Y'))
                # dump everthing to destination file
                dump_json(sorted_data,args.destination)
    # source is not given
    # the script will parse the standard input data
    # i.e. cat somefile | python errpt-a_to_json.py
    else:
        result = parse_string(sys.stdin.read())
        print(json.dumps(result, indent=4))
                        

if __name__ == "__main__":
    main()
