import argparse
import xml.etree.ElementTree as ET
from collections import defaultdict
from pprint import pprint
import operator
import glob
import os
import csv
import librosa
#import regex as re

def parse_speakers(trans):
    global args
    global spks
    global csvs

    # parse Speakers section
    speakers = trans.find('Speakers')
    assert speakers is not None
    for speaker in speakers.findall('Speaker'):
        spk = dict(speaker.attrib)
        spk['folder_name'] = spk['name'].replace(' ', '_')
        #spk['folder_name'] = "{sane_name}_{type}_{dialect}_{accent}_{scope}".format(**spk)
        spks[spk['id']] = spk

        # create speaker folder if does not exist
        folder_path = os.path.join(args.speaker_dir, spk['folder_name'])
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)

        # open CSV file if not opened yet
        if spk['name'] not in csvs:
            file_path = os.path.join(folder_path, 'sentences.csv')
            csvfile = open(file_path, 'w', newline='', encoding='utf-8')
            csvwriter = csv.writer(csvfile)
            csvs[spk['name']] = csvwriter

def parse_episodes(trans):
    for episode in trans.findall('Episode'):
        for section in episode:
            assert section.tag == 'Section', "Episode is expected to contain only sections"
            # ignore nontrans sections
            if section.attrib['type'] == 'nontrans':
                continue
            section_type = section.attrib['type']
            section_types[section_type] += 1
            section_start = section.attrib['startTime']
            section_end = section.attrib['endTime']
            for turn in section:
                assert turn.tag == 'Turn', "Section is expected to contain only turns"
                # ignore turns that are not associated with speaker
                if 'speaker' not in turn.attrib:
                    continue
                speaker = turn.attrib['speaker']

                # log statistics
                if 'mode' in turn.attrib:
                    turn_modes[turn.attrib['mode']] += 1
                if 'fidelity' in turn.attrib:
                    turn_fidelities[turn.attrib['fidelity']] += 1
                if 'channel' in turn.attrib:
                    turn_channels[turn.attrib['channel']] += 1

                # parse audio segments
                turn_start = turn.attrib['startTime']
                turn_end = turn.attrib['endTime']
                current_text = turn.text.strip()
                current_time = turn_start
                skip = False
                for elem in turn:
                    if elem.tag == 'Sync':
                        sync_time = elem.attrib['time']
                        if current_text is not None and current_text != '':
                            write_segment(float(current_time), float(sync_time), current_text, speaker, section.attrib, turn.attrib)
                        current_time = sync_time
                        current_text = ''
                    elif elem.tag == 'Event':
                        # log statistics
                        event_descs[elem.attrib['desc']] += 1
                        event_types[elem.attrib['type']] += 1
                        event_extents[elem.attrib['extent']] += 1

                        # stop processing till next sync
                        if current_text is None:
                            continue

                        if elem.attrib['type'] == 'noise':
                            # r - breathing
                            # b - mumbling ("ee"), usually in interviews
                            # bg - coughing, very few instances, only in interviews
                            # bb - mouth/tongue noise
                            # pf - voluntary sigh, only once
                            # pap - turning page
                            # jingle - mostly in start and end turns, which are not associated with speaker
                            # applaude - selfexplanatory, only three times in interviews
                            # musique - selfexplanatory, only three times in interviews
                            # conv - background conversation (with begin and end)
                            assert elem.attrib['desc'] in ['r', 'b', 'bg', 'bb', 'pf', 'pap', 'jingle', 'applaude', 'musique', 'nontrans', 'conv'], "Unexpected noise description: " + elem.attrib['desc']
                            assert elem.attrib['extent'] == 'instantaneous' or (elem.attrib['desc'] in ['conv', 'bg', 'musique'] and elem.attrib['extent'] in ['begin', 'end']), "Unexpected noise extent: " + elem.attrib['extent']
                            if elem.attrib['extent'] == 'begin':
                                skip = True
                                current_text = ''
                                continue
                            elif elem.attrib['extent'] == 'end':
                                skip = False
                                current_text = None
                                continue
                            elif elem.attrib['desc'] in ['jingle', 'applaude', 'nontrans']:
                                # discard segments with jingles, applauses and music
                                current_text = None
                                continue
                            else:
                                # add special tag to the text
                                current_text = (current_text + ' [%s]' % elem.attrib['desc']).strip()
                        elif elem.attrib['type'] == 'language':
                            assert elem.attrib['extent'] in ['begin', 'end', 'instantaneous', 'previous'], "Unexpected extent for language: " + elem.attrib['extent']
                            # disable generation of this segment
                            current_text = None
                            continue
                        elif elem.attrib['type'] == 'pronounce':
                            assert elem.attrib['extent'] in ['previous', 'next', 'begin', 'end', 'instantaneous'], "Unexpected extent for pronounuce: " + elem.attrib['extent']
                            '''
                            if elem.attrib['extent'] in ['previous', 'instantaneous']:
                                words = elem.attrib['desc'].split(' ')
                                if len(words) > 1:
                                    print("previous:", words)
                                    print(current_text)
                                # try to replace capitalized acronyms
                                current_text, n = re.subn(r'\b[\p{Lu}\d]{%d}$' % len(words), elem.attrib['desc'], current_text)
                                if n == 0:
                                    # replace N last words with pronouncation
                                    current_text = re.sub(r'\w+(\W+\w+){%d}$' % (len(words) - 1), elem.attrib['desc'], current_text)
                                if len(words) > 1:
                                    print(current_text)
                            elif elem.attrib['extent'] == 'next':
                                words = elem.attrib['desc'].split(' ')
                                if len(words) > 1:
                                    print("next:", words)
                                    print(elem.tail)
                                # try to replace capitalized acronyms
                                elem.tail, n = re.subn(r'^[\p{Lu}\d]{%d}\b' % len(words), elem.attrib['desc'], elem.tail)
                                if n == 0:
                                    # replace N next words with pronouncation
                                    elem.tail = re.sub(r'^(\w+\W+){%d}\w+' % (len(words) - 1), elem.attrib['desc'], elem.tail)
                                if len(words) > 1:
                                    print(elem.tail)
                            elif elem.attrib['extent'] == 'begin':
                                # ignore text within
                                elem.tail = ''
                            elif elem.attrib['extent'] == 'end':
                                current_text = (current_text + ' ' + elem.attrib['desc']).strip()
                            '''
                        else:
                            assert False, "Unknown event type: " + elem.attrib['type']
                    else:
                        assert False, "Turn is expected to have only sync and event tags, got " + elem.tag

                    if not skip:
                        current_text = (current_text + ' ' + elem.tail.strip()).strip()
                    else:
                        current_text = ''

                if current_text is not None and current_text != '':
                    write_segment(float(current_time), float(turn_end), current_text, speaker, section.attrib, turn.attrib)

def write_segment(start_time, end_time, text, speaker, section, turn):
    global args
    global spks
    global csvs
    global audio_filename
    global audio
    global sample_rate

    spk = spks[speaker]
    csvwriter = csvs[spk['name']]

    # construct file name for sentence wav
    filename = "{0}_{1}_{2}".format(audio_filename, start_time, end_time)
    if 'mode' in turn:
        filename += '_' + turn['mode']
    if 'fidelity' in turn:
        filename += '_' + turn['fidelity']
    if 'channel' in turn:
        filename += '_' + turn['channel']
    filename += '.wav'
    file_path = os.path.join(args.speaker_dir, spk['folder_name'], filename)

    # cut the sentence wav and save to file
    start_sample = librosa.time_to_samples(start_time, sample_rate)
    end_sample = librosa.time_to_samples(end_time, sample_rate)
    wav = audio[start_sample:end_sample]
    if args.trim_top_db:
        wav, idx = librosa.effects.trim(wav, top_db=args.trim_top_db)
    librosa.output.write_wav(file_path, wav, sample_rate)
    # add sentence to CSV file
    csvwriter.writerow([filename, text])

    # log statistics
    global speaker_times
    global total_time
    #print(spk['name'], start_time, end_time, text)
    duration = end_time - start_time
    assert duration > 0
    speaker_times[spk['name']] += duration
    total_time += duration

parser = argparse.ArgumentParser()
parser.add_argument('--trans_files', default='*.trs')
parser.add_argument('--trans_dir', default='trans')
parser.add_argument('--audio_dir', default='audio')
parser.add_argument('--speaker_dir', default='speakers')
parser.add_argument('--trim_top_db', type=float)
parser.add_argument('--sample_rate', type=int)
args = parser.parse_args()

if not os.path.isdir(args.speaker_dir):
    os.mkdir(args.speaker_dir)

speaker_times = defaultdict(int)
total_time = 0
section_types = defaultdict(int)
turn_modes = defaultdict(int)
turn_fidelities = defaultdict(int)
turn_channels = defaultdict(int)
event_descs = defaultdict(int)
event_types = defaultdict(int)
event_extents = defaultdict(int)

csvs = {}

trans_match = os.path.join(args.trans_dir, args.trans_files)
for trans_filename in glob.glob(trans_match):
    print(trans_filename)
    tree = ET.parse(trans_filename)
    trans = tree.getroot()
    assert trans.tag == 'Trans'
    audio_filename = trans.attrib['audio_filename']
    audio_path = os.path.join(args.audio_dir, audio_filename + '.wav')
    audio, sample_rate = librosa.load(audio_path, sr=args.sample_rate)

    spks = {}
    parse_speakers(trans)
    parse_episodes(trans)

print("Speaker times:")
pprint(sorted(speaker_times.items(), key=operator.itemgetter(1)))
print("Total time:", total_time)
print("Section types:", dict(section_types))

print("Turn modes:", dict(turn_modes))
print("Turn fidelities:", dict(turn_fidelities))
print("Turn channels:", dict(turn_channels))

print("Event descs:", dict(event_descs))
print("Event types:", dict(event_types))
print("Event extents:", dict(event_extents))
