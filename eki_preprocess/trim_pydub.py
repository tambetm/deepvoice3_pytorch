import argparse
from pydub import AudioSegment
import glob
import os

def detect_leading_silence(sound, silence_threshold=-50.0, chunk_size=10):
    '''
    sound is a pydub.AudioSegment
    silence_threshold in dB
    chunk_size in ms

    iterate over chunks until you find the first one with sound
    '''
    trim_ms = 0 # ms

    assert chunk_size > 0 # to avoid infinite loop
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        #trim_ms += chunk_size
        trim_ms += 1

    return trim_ms

parser = argparse.ArgumentParser()
parser.add_argument('--input_files', default='*.wav')
parser.add_argument('--input_dir', default='eva')
parser.add_argument('--output_dir', default='eva_trimmed_pydub')
parser.add_argument('--chunk_size', type=int, default=10)
parser.add_argument('--silence_threshold_begin', type=float, default=-33.0)
parser.add_argument('--silence_threshold_end', type=float, default=-47.0)
args = parser.parse_args()

if not os.path.isdir(args.output_dir):
    os.mkdir(args.output_dir)

input_match = os.path.join(args.input_dir, args.input_files)
for filename in glob.glob(input_match):
    print(filename, end='')
    sound = AudioSegment.from_wav(filename)
    start_trim = detect_leading_silence(sound, args.silence_threshold_begin, args.chunk_size)
    end_trim = detect_leading_silence(sound.reverse(), args.silence_threshold_end, args.chunk_size)
    print(" ", start_trim, end_trim)
    trimmed_sound = sound[start_trim:len(sound) - end_trim]
    output_filename = os.path.join(args.output_dir, os.path.basename(filename))
    trimmed_sound.export(output_filename, format="wav")
