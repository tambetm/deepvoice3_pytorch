import argparse
import falcon
from hparams import hparams, hparams_debug_string
import os
from synthesizer import Synthesizer


html_body = '''<html><title>Demo</title>
<meta charset="UTF-8">
<style>
body {padding: 16px; font-family: sans-serif; font-size: 14px; color: #444}
input, select {font-size: 14px; padding: 8px 12px; outline: none; border: 1px solid #ddd}
input:focus, select:focus {box-shadow: 0 1px 2px rgba(0,0,0,.15)}
p {padding: 12px}
button {background: #28d; padding: 9px 14px; margin-left: 8px; border: none; outline: none;
        color: #fff; font-size: 14px; border-radius: 4px; cursor: pointer;}
button:hover {box-shadow: 0 1px 2px rgba(0,0,0,.15); opacity: 0.9;}
button:active {background: #29f;}
button[disabled] {opacity: 0.4; cursor: default}
</style>
<body>
<form>
  <select id="speaker">
    <option value="0">Meelis Kompus</option>
    <option value="1">Tarmo Maiberg</option>
    <option value="2">Birgit Itse</option>
    <option value="3">Vallo Kelmsaar</option>
    <option value="4">Indrek Kiisler</option>
    <option value="5">Tõnu Karjatse</option>
    <option value="6">Kai Vare</option>
  </select>
  <input id="text" type="text" size="40" placeholder="Enter Text">
  <button id="button" name="synthesize">Speak</button>
</form>
<p id="message"></p>
<audio id="audio" controls autoplay hidden></audio>
<script>
function q(selector) {return document.querySelector(selector)}
q('#text').focus()
q('#button').addEventListener('click', function(e) {
  text = q('#text').value.trim()
  speaker_id = q('#speaker').value
  if (text) {
    q('#message').textContent = 'Synthesizing...'
    q('#button').disabled = true
    q('#audio').hidden = true
    synthesize(text, speaker_id)
  }
  e.preventDefault()
  return false
})
function synthesize(text, speaker_id) {
  fetch('/synthesize?text=' + encodeURIComponent(text) + '&speaker_id=' + encodeURIComponent(speaker_id), {cache: 'no-cache'})
    .then(function(res) {
      if (!res.ok) throw Error(response.statusText)
      return res.blob()
    }).then(function(blob) {
      q('#message').textContent = ''
      q('#button').disabled = false
      q('#audio').src = URL.createObjectURL(blob)
      q('#audio').hidden = false
    }).catch(function(err) {
      q('#message').textContent = 'Error: ' + err.message
      q('#button').disabled = false
    })
}
</script></body></html>
'''


class UIResource:
  def on_get(self, req, res):
    res.content_type = 'text/html'
    res.body = html_body


class SynthesisResource:
  def on_get(self, req, res):
    if not req.params.get('text') or not req.params.get('speaker_id'):
      raise falcon.HTTPBadRequest()
    res.data = synthesizer.synthesize(req.params.get('text'), int(req.params.get('speaker_id')))
    res.content_type = 'audio/wav'
    res.set_header('Access-Control-Allow-Origin', '*')
    #res.set_header("Access-Control-Expose-Headers: Access-Control-Allow-Origin")
    #res.set_header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept')

synthesizer = Synthesizer()
api = falcon.API()
api.add_route('/synthesize', SynthesisResource())
api.add_route('/', UIResource())


if __name__ == '__main__':
  from wsgiref import simple_server
  parser = argparse.ArgumentParser()
  parser.add_argument('--checkpoint', help='Full path to model checkpoint', default='checkpoints/uudised/checkpoint_step001260000.pth')
  parser.add_argument('--port', type=int, default=9000)
  parser.add_argument('--hparams', default='preset=deepvoice3_erm',
    help='Hyperparameter overrides as a comma-separated list of name=value pairs')
  args = parser.parse_args()
  os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
  hparams.parse(args.hparams)
  print(hparams_debug_string())
  synthesizer.load(args.checkpoint)
  print('Serving on port %d' % args.port)
  simple_server.make_server('0.0.0.0', args.port, api).serve_forever()
else:
  synthesizer.load(os.environ['CHECKPOINT'])
