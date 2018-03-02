import argparse
import glob
import csv
import os

parser = argparse.ArgumentParser()
parser.add_argument('input_dir')
args = parser.parse_args()

with open(os.path.join(args.input_dir, 'train.txt'), 'w') as of:
    csvwriter = csv.writer(of, delimiter='|', quotechar='*')
    for dir in glob.glob(os.path.join(args.input_dir, '*')):
        if not os.path.isdir(dir):
            continue
        reldir = os.path.relpath(dir, args.input_dir)
        with open(os.path.join(dir, 'train.txt'), encoding='utf-8') as f:
            csvreader = csv.reader(f, delimiter='|')
            for data in csvreader:
                data[0] = os.path.join(reldir, data[0])
                data[1] = os.path.join(reldir, data[1])
                csvwriter.writerow(data)
