# coding: utf-8

"""Text processing frontend

All frontend module should have the following functions:

- text_to_sequence(text, p)
- sequence_to_text(sequence)

and the property:

- n_vocab

"""
from deepvoice3_pytorch.frontend import en
from deepvoice3_pytorch.frontend import et_er
from deepvoice3_pytorch.frontend import et_er_lowercase
from deepvoice3_pytorch.frontend import et_eva
from deepvoice3_pytorch.frontend import et_eva_lowercase

# optinoal Japanese frontend
try:
    from deepvoice3_pytorch.frontend import jp
except ImportError:
    jp = None

try:
    from deepvoice3_pytorch.frontend import ko
except ImportError:
    ko = None

