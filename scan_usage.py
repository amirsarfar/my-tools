import os
import argparse
import requests
import json
import time
from tqdm import tqdm

parser = argparse.ArgumentParser()

parser.add_argument("--rel", action="store_true", help="Relative target directory")
parser.add_argument("-t", help="Target directory for tokens to search")
parser.add_argument("-r", help="Root directory path to search")
parser.add_argument("-e", help="File extensions to search separated by space")

args = parser.parse_args()

rootdir = args.r or "./"
file_extensions = (args.e or ".js .jsx").split(" ")
target_file = args.t if not args.rel else rootdir + args.t
print(target_file, file_extensions)
tokens = []
tokens_dict = {}


def scan(root=rootdir):
    for folder, dirs, files in os.walk(root):
        for file in files:
            yield os.path.join(folder, file)


def get_js_parsed_ast(file_content):
    resp = requests.post(
        "http://127.0.0.1:3000/parse",
        data=file_content.encode("utf-8"),
        headers={"content-type": "text/plain"},
    )
    return json.loads(resp.text)["ast"]["body"]


for fullpath in scan(target_file):
    if any(fullpath.endswith(x) for x in [".js"]):
        with open(fullpath, "r") as f:
            identifiers = get_js_parsed_ast(f.read())
            for identifier in identifiers:
                if identifier["type"] == "ExportNamedDeclaration":
                    main_dec = identifier["declaration"]
                    if main_dec != None and main_dec["type"] == "FunctionDeclaration":
                        tokens.append(main_dec["id"]["name"])
                        tokens_dict[main_dec["id"]["name"]] = (
                            fullpath + ":" + str(main_dec["loc"]["start"]["line"])
                        )
                    if main_dec != None and main_dec["type"] == "VariableDeclaration":
                        for declaration in main_dec["declarations"]:
                            tokens.append(declaration["id"]["name"])
                            tokens_dict[declaration["id"]["name"]] = (
                                fullpath + ":" + str(main_dec["loc"]["start"]["line"])
                            )


filecounter = 0
for filepath in scan():
    filecounter += 1

used_tokens = set()
log_filename = "usage_scan_" + str(int(time.time())) + ".log"
for fullpath in tqdm(scan(), total=filecounter, unit="files"):
    if any(fullpath.endswith(x) for x in file_extensions):
        with open(fullpath, "r") as f:
            identifiers = get_js_parsed_ast(f.read())
            for identifier in identifiers:
                if identifier["type"] == "ImportDeclaration":
                    for specifier in identifier["specifiers"]:
                        if (
                            specifier["type"] == "ImportSpecifier"
                            and specifier["imported"]["name"] in tokens
                        ):
                            used_tokens.add(specifier["imported"]["name"])
                            with open(log_filename, "a+") as myfile:
                                myfile.write(
                                    "\n"
                                    + specifier["imported"]["name"]
                                    + " -> "
                                    + specifier["local"]["name"]
                                    + " | "
                                    + fullpath
                                )


def filter_func(token):
    return token not in used_tokens


def map_func(token):
    return token + " " + tokens_dict[token]


unused_tokens = list(map(map_func, filter(filter_func, tokens)))
un_log_filename = "usage_scan_unused_" + str(int(time.time())) + ".log"
with open(un_log_filename, "a+") as myfile:
    myfile.write("Unused tokens: \n" + "\n".join(unused_tokens))
print("\n\nLog file: ", log_filename)
