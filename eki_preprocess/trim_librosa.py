import argparse
import librosa
import glob
import os

parser = argparse.ArgumentParser()
parser.add_argument('--input_files', default='*.wav')
parser.add_argument('--input_dir', default='eva')
parser.add_argument('--output_dir', default='eva_trimmed')
parser.add_argument('--sample_rate', type=int)
parser.add_argument('--top_db', type=int, default=60)
args = parser.parse_args()

if not os.path.isdir(args.output_dir):
    os.mkdir(args.output_dir)

input_match = os.path.join(args.input_dir, args.input_files)
for filename in glob.glob(input_match):
    print(filename, end='')
    wav, sample_rate = librosa.load(filename, sr=args.sample_rate)
    wav, idx = librosa.effects.trim(wav, top_db=args.top_db)
    print(idx)
    output_filename = os.path.join(args.output_dir, os.path.basename(filename))
    librosa.output.write_wav(output_filename, wav, sample_rate)
