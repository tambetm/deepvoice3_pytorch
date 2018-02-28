# coding: utf-8

symbols = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!\'()[],-.:;? ÕÄÖÜŠŽõäöüšž"“„’*'
n_vocab = len(symbols)

def text_to_sequence(text, p=0.0):
    from deepvoice3_pytorch.frontend.text import text_to_sequence
    text = text_to_sequence(text, ["estonian_cleaners_er"])
    return text


from deepvoice3_pytorch.frontend.text import sequence_to_text
