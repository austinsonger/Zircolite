#!python3
# -*- coding: utf-8 -*-

import os
import subprocess
import argparse
import yaml
import glob
import json
import binascii
import sys
from multiprocessing import Pool

parser = argparse.ArgumentParser()
parser.add_argument("--rulesdirectory", help="Sub-directory generated by rules-search", type=str)
parser.add_argument("--sigmac", help="Sigmac location", type=str, required=True)
parser.add_argument("--output", help="Converted rules output filename", default="rules.json", type=str)
parser.add_argument("--config", help="Sigmac config location", type=str, required=True)
parser.add_argument("--rule", help="Rule file", type=str)
parser.add_argument("--table", help="Table name", default="logs", type=str)
parser.add_argument("--fileext", help="Rule file extension", default="yml", type=str)
args = parser.parse_args()

def CRC32_from_string(string):
    buf = (binascii.crc32(bytes(str(string), "utf-8")) & 0xFFFFFFFF)
    return "%08X" % buf   

def retrieveRule(ruleFile):
    d={}
    cmd = [args.sigmac, "-d", "--target", "sqlite", "-c", args.config, ruleFile,"--backend-option","table=logs"]
    output = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.read()
    if "unsupported" in str(output):
        return d.copy()
    else:
        output = output.decode('UTF-8').split("\n")
        output = [expr.replace("{}", args.table) for expr in output]
        with open(ruleFile, 'r') as stream:
            docs = yaml.load_all(stream, Loader=yaml.FullLoader)
            for doc in docs:
                for k,v in doc.items():
                    if k=='title':
                        title=v
                    if k=='id':
                        d['title']=title + " - " + CRC32_from_string(v)
                    if k=='description':
                        d['description']=v
                    if k=='tags':
                        d['tags']=v
                    if k=='level':
                        d['level']=v
                    if k=='author':
                        d['author']=v
        if output[:-1] == "":
            print(output)
        d['rule']=output[:-1]
        return d.copy()

if __name__ == '__main__':
    if not os.path.exists(args.sigmac):
        print("Cannot find sigmac rule converter please set a correct location via '--sigmac'")
        sys.exit(1)
    if args.rule:
        outputList = retrieveRule(args.rule)
    else:
        files = glob.glob(args.rulesdirectory + "/**/*." + args.fileext, recursive=True)
        pool = Pool()
        outputList = pool.map(retrieveRule, files)
        pool.close() 
        pool.join()

    outputList = list(filter(None, outputList)) # Remove empty rules
    with open(args.output, 'w') as f:
        if args.rule is not None:
            json.dump([outputList], f, indent=4)
        else : 
            json.dump(outputList, f, indent=4)
