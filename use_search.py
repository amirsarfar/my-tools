import os
import argparse

parser=argparse.ArgumentParser()

parser.add_argument("-c", help="Component")
parser.add_argument("-p", help="Prop")
parser.add_argument("-d", help="Line distance limit between component and prop")
parser.add_argument("-r", help="Directory path to search")
parser.add_argument("-e", help="File extensions to search separated by space")

args=parser.parse_args()

component = args.c
prop = args.p
if not component or not prop:
  print("The component and prop options are required")
  exit()
padding = int(args.d or 1000000)
rootdir = (args.r or "./")
file_extensions = (args.e or "").split(" ")

for folder, dirs, files in os.walk(rootdir):
  for file in files:
    if any(file.endswith(x) for x in file_extensions):
      fullpath = os.path.join(folder, file)
      flag = 0
      with open(fullpath, 'r') as f:
        for idx, line in enumerate(f):
          if prop in line and flag <= padding:
            print(fullpath + ":" + str(idx + 1))
          if component in line:
            flag = 0
          flag += 1
