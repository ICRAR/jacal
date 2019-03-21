import os
import csv
import argparse


def absolute_paths(directory):
   for dirpath,_,filenames in os.walk(directory):
       for f in filenames:
           yield os.path.abspath(os.path.join(dirpath, f))

def generate_file(directory, output):
    with open(output, 'w') as csvfile:
        writer = csv.writer(csvfile)
        for path in absolute_paths(directory):
            file_name = os.path.splitext(os.path.basename(path))[0]
            freq = float(file_name.split('_')[3].replace('f', ''))*10**6
            writer.writerow([int(round(freq)), path])

def main():
    parser = argparse.ArgumentParser(description='Generate eor sky model file lookup.')
    parser.add_argument('--dir', dest='directory', required=True,
                        help='eor sky model directory.')
    parser.add_argument('--out', dest='output',
                        help='csv output file.', type=str, required=True)

    args = parser.parse_args()

    generate_file(args.directory, args.output)

if __name__ == '__main__':
    main()
