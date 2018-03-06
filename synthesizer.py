import io
import numpy as np
import torch
from torch.autograd import Variable
from hparams import hparams
from deepvoice3_pytorch import frontend
import audio


class Synthesizer:
  def load(self, checkpoint_path, fast=True):
    # Presets
    if hparams.preset is not None and hparams.preset != "":
        preset = hparams.presets[hparams.preset]
        import json
        hparams.parse_json(json.dumps(preset))
        print("Override hyper parameters with preset \"{}\": {}".format(
            hparams.preset, json.dumps(preset, indent=4)))

    self._frontend = getattr(frontend, hparams.frontend)
    import train
    train._frontend = self._frontend
    from train import build_model

    # Model
    self.model = build_model()

    # Load checkpoints separately
    checkpoint = torch.load(checkpoint_path)
    self.model.load_state_dict(checkpoint["state_dict"])
    #model.seq2seq.decoder.max_decoder_steps = max_decoder_steps

    self.use_cuda = torch.cuda.is_available()
    if self.use_cuda:
        self.model = self.model.cuda()
    self.model.eval()
    if fast:
        self.model.make_generation_fast_()



  def synthesize(self, text, speaker_id=0):
    """Convert text to speech waveform given a deepvoice3 model.

    Args:
        text (str) : Input text to be synthesized
        p (float) : Replace word to pronounciation if p > 0. Default is 0.
    """
    sequence = np.array(self._frontend.text_to_sequence(text))
    sequence = Variable(torch.from_numpy(sequence)).unsqueeze(0)
    text_positions = torch.arange(1, sequence.size(-1) + 1).unsqueeze(0).long()
    text_positions = Variable(text_positions)
    speaker_ids = None if speaker_id is None else Variable(torch.LongTensor([speaker_id]))
    if self.use_cuda:
        sequence = sequence.cuda()
        text_positions = text_positions.cuda()
        speaker_ids = None if speaker_ids is None else speaker_ids.cuda()

    # Greedy decoding
    mel_outputs, linear_outputs, alignments, done = self.model(
        sequence, text_positions=text_positions, speaker_ids=speaker_ids)

    linear_output = linear_outputs[0].cpu().data.numpy()

    # Predicted audio signal
    waveform = audio.inv_spectrogram(linear_output.T)
    out = io.BytesIO()
    audio.save_wav(waveform, out)
    return out.getvalue()
