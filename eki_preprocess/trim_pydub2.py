import argparse
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import glob
import os

parser = argparse.ArgumentParser()
parser.add_argument('--input_files', default='*.wav')
parser.add_argument('--input_dir', default='Evas_jagamiseks')
parser.add_argument('--output_dir', default='Evas_trimmed_pydub')
parser.add_argument('--min_silence_len', type=int, default=10)
parser.add_argument('--seek_step', type=int, default=1)
parser.add_argument('--silence_threshold', type=float, default=-45.0)
parser.add_argument('--cut_begin', type=int, default=400)
args = parser.parse_args()

if not os.path.isdir(args.output_dir):
    os.mkdir(args.output_dir)

input_match = os.path.join(args.input_dir, args.input_files)
for filename in glob.glob(input_match):
    print(filename, end='')
    sound = AudioSegment.from_wav(filename)
    if args.cut_begin:
        sound = sound[args.cut_begin:]
    idx = detect_nonsilent(sound, min_silence_len=args.min_silence_len, silence_thresh=args.silence_threshold, seek_step=args.seek_step)
    if len(idx) > 0:
        start_trim = idx[0][0]
        end_trim = idx[-1][1]
        print(" ", start_trim, end_trim)
        sound = sound[start_trim:end_trim]
    else:
        print(" all silent?")
    output_filename = os.path.join(args.output_dir, os.path.basename(filename))
    sound.export(output_filename, format="wav")
