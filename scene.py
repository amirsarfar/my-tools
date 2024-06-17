import os
import argparse
import requests
import json
import time
from tqdm import tqdm

parser = argparse.ArgumentParser()
# python scene.py -r /home/amir/code/RTProSLWeb-Front/src -t / --rel
parser.add_argument("--rel", action="store_true", help="Relative target directory")
parser.add_argument("-t", help="Target directory for tokens to search")
parser.add_argument("-r", help="Root directory path to search")
parser.add_argument("-e", help="File extensions to search separated by space")

args = parser.parse_args()

rootdir = args.r or "./"
file_extensions = (args.e or ".js .jsx").split(" ")
target_file = args.t if not args.rel else rootdir + args.t
print(target_file, file_extensions)

the_dict = {}
timee = int(time.time())


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
                    if not fullpath in the_dict:
                        the_dict[fullpath] = {}
                    if main_dec != None and main_dec["type"] == "FunctionDeclaration":
                        the_dict[fullpath][main_dec["id"]["name"]] = {
                            "line": main_dec["loc"]["start"]["line"],
                            "local": False,
                            "external": False,
                        }
                    if main_dec != None and main_dec["type"] == "VariableDeclaration":
                        for dec in main_dec["declarations"]:
                            the_dict[fullpath][dec["id"]["name"]] = {
                                "line": main_dec["loc"]["start"]["line"],
                                "local": False,
                                "external": False,
                            }

filecounter = 0
for filepath in scan():
    filecounter += 1


def match_import_path(imp):

    def checkDastanz(p):
        if os.path.exists(p + "/index.js"):
            return p + "/index.js"
        if os.path.exists(p + "/index.jsx"):
            return p + "/index.jsx"
        if os.path.exists(p + ".js"):
            return p + ".js"
        if os.path.exists(p + ".jsx"):
            return p + ".jsx"
        return None

    if imp.startswith("."):
        new_imp = []
        c = 1
        for part in imp.split("/"):
            if part == ".":
                continue
            if part == "..":
                c += 1
            else:
                new_imp.append(part)
        new_imp = "/".join(new_imp)
        new_path = "/".join(fullpath.split("/")[:-c])
        pathi = os.path.join(new_path, new_imp)
        return checkDastanz(pathi)

    return checkDastanz("/home/amir/code/RTProSLWeb-Front/src/" + imp)


# for fullpath in scan():
for fullpath in tqdm(scan(), total=filecounter, unit="files"):
    if any(fullpath.endswith(x) for x in file_extensions):
        with open(fullpath, "r") as f:
            identifiers = get_js_parsed_ast(f.read())
            for identifier in identifiers:
                if fullpath == "/home/amir/code/RTProSLWeb-Front/src/utilities/constants/grid/comboGrid/models.js" and identifier[
                    "type"
                ] in [
                    "ImportDeclaration",
                ]:
                    print(identifier)
                if identifier["type"] == "ImportDeclaration":
                    true_path = match_import_path(identifier["source"]["value"])
                    if true_path != None and true_path in the_dict:
                        for specifier in identifier["specifiers"]:
                            if (
                                specifier["type"] == "ImportSpecifier"
                                and specifier["imported"]["name"] in the_dict[true_path]
                            ):
                                the_dict[true_path][specifier["imported"]["name"]][
                                    "external"
                                ] = True
                            if specifier["type"] == "ImportNamespaceSpecifier":
                                for var_name in the_dict[true_path]:
                                    the_dict[true_path][var_name]["external"] = True


un_log_filename = "usage_scan_unused_" + str(timee) + ".log"
with open(un_log_filename, "a+") as myfile:
    myfile.write("Unused tokens: \n\n")
    for file_name, vars in the_dict.items():
        f = False
        for var_name, detail in vars.items():
            if not detail["local"] and not detail["external"]:
                if not f:
                    myfile.write("--" + file_name + ":\n")
                    f = True
                myfile.write(
                    var_name + " " + file_name + ":" + str(detail["line"]) + "\n"
                )


print("\n\nUnused log file: ", un_log_filename)
