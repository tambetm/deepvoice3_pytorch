import os
import argparse
from flask import Flask, render_template, request, abort, send_file
from hparams import hparams, hparams_debug_string
from synthesizer import Synthesizer

parser = argparse.ArgumentParser()
parser.add_argument('--checkpoint', help='Full path to model checkpoint', default='checkpoints/uudised/checkpoint_step001270000.pth')
parser.add_argument('--hparams', default='preset=deepvoice3_erm', help='Hyperparameter overrides as a comma-separated list of name=value pairs')
parser.add_argument('--host', default='0.0.0.0')
parser.add_argument('--port', type=int, default=9000)
args = parser.parse_args()

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
hparams.parse(args.hparams)
print(hparams_debug_string())

synthesizer = Synthesizer()
synthesizer.load(args.checkpoint)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route("/", methods=['GET'])
def demo():
    return render_template('demo.html')

@app.route("/synthesize", methods=['GET'])
def synthesize():
    text = request.args.get('text', '')
    speaker_id = request.args.get('speaker_id', '')
    if text == '' or speaker_id == '':
        abort(404)
    data = synthesizer.synthesize(text, int(speaker_id))
    return send_file(data, mimetype='audio/wav')

if __name__ == '__main__':
    app.run(args.host, args.port)
