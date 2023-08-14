import os
import argparse

parser=argparse.ArgumentParser()

parser.add_argument("--rel", action="store_true", help="Relative target file")
parser.add_argument("-t", help="Target file for tokens to search")
parser.add_argument("-i", help="Import name search")
parser.add_argument("-r", help="Directory path to search")
parser.add_argument("-e", help="File extensions to search separated by space")

args=parser.parse_args()

rootdir = (args.r or "./")
file_extensions = (args.e or "").split(" ")
target_file = args.t if not args.rel else  rootdir + args.t
import_search = args.i

tokens = []
with open(target_file, 'r') as f:
  for idx, line in enumerate(f):
    if line.startswith("export const"):
      parts = line.split(" ")
      print(parts[2])
      tokens.append(parts[2])
    if line.startswith("export function"):
      parts = line.split(" ")
      print(parts[2].split("(")[0])
      tokens.append(parts[2].split("(")[0])

used_tokens = set()
for folder, dirs, files in os.walk(rootdir):
  for file in files:
    if any(file.endswith(x) for x in file_extensions):
      fullpath = os.path.join(folder, file)
      with open(fullpath, 'r') as f:
        imported = False
        for idx, line in enumerate(f):
          cri = False
          if import_search in line:
            print("import", fullpath + ":" + str(idx + 1))
            imported = True
            cri = True
          if imported and not cri:
            for token in tokens:
              if token in line:
                used_tokens.add(token)
                print(token, fullpath + ":" + str(idx + 1))

def filter_func(token):
  return token not in used_tokens
unused_tokens = list(filter(filter_func, tokens))
print("Unused tokens: ", unused_tokens)
