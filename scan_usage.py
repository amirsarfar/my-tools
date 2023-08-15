import os
import argparse
import requests
import json
import time
from tqdm import tqdm

parser=argparse.ArgumentParser()

parser.add_argument("--rel", action="store_true", help="Relative target file")
parser.add_argument("-t", help="Target file for tokens to search")
parser.add_argument("-r", help="Directory path to search")
parser.add_argument("-e", help="File extensions to search separated by space")

args=parser.parse_args()

rootdir = (args.r or "./")
file_extensions = (args.e or "").split(" ")
target_file = args.t if not args.rel else  rootdir + args.t

tokens = []
tt = {}
def scan(root=rootdir):
  for folder, dirs, files in os.walk(root):
    for file in files:
      yield os.path.join(folder, file)

for fullpath in scan(target_file):
  if any(fullpath.endswith(x) for x in [".js"]):
    with open(fullpath, 'r') as f:
      cc = f.read()
      resp = requests.post("http://127.0.0.1:3000/parse", data=cc.encode("utf-8"), headers={"content-type":"text/plain"})
      js = json.loads(resp.text)["ast"]["body"]
      for ide in js:
        if ide["type"] == "ExportNamedDeclaration":
          if ide["declaration"]["type"] == "FunctionDeclaration":
            tokens.append(ide["declaration"]["id"]["name"])
            tt[ide["declaration"]["id"]["name"]] = fullpath + ":" + str(ide["declaration"]["loc"]["start"]["line"])
            print(ide["declaration"]["type"], ide["declaration"]["id"]["name"], ide["declaration"]["loc"])
          if ide["declaration"]["type"] == "VariableDeclaration":
            tokens.append(ide["declaration"]["declarations"][0]["id"]["name"])
            tt[ide["declaration"]["declarations"][0]["id"]["name"]] = fullpath + ":" + str(ide["declaration"]["loc"]["start"]["line"])
            print(ide["declaration"]["type"], ide["declaration"]["declarations"][0]["id"]["name"], ide["declaration"]["loc"])


filecounter = 0
for filepath in scan():
  filecounter += 1

used_tokens = set()
log_filename = "usage_scan"+ str(int(time.time())) +".log"
for fullpath in tqdm(scan(), total=filecounter, unit="files"):
  if any(fullpath.endswith(x) for x in file_extensions):
    with open(fullpath, 'r') as f:
      cc = f.read()
      resp = requests.post("http://127.0.0.1:3000/parse", data=cc.encode("utf-8"), headers={"content-type":"text/plain"})
      js = json.loads(resp.text)["ast"]["body"]
      for ide in js:
        if ide["type"] == "ImportDeclaration":
          for specifier in ide["specifiers"]:
            if specifier["type"] == "ImportSpecifier" and specifier["imported"]["name"] in tokens:
              used_tokens.add(specifier["imported"]["name"])
              with open(log_filename, "a") as myfile:
                myfile.write("\n" + specifier["imported"]["name"] + " -> " + specifier["local"]["name"] + " | " + fullpath)

def filter_func(token):
  return token not in used_tokens
def map_func(token):
  return token + " " + tt[token]
unused_tokens = list(map(map_func, filter(filter_func, tokens)))
print("Unused tokens: ", "\n".join(unused_tokens))
