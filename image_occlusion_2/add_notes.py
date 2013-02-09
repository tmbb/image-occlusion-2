import etree.ElementTree as etree

from anki import notes, consts
from anki.consts import MODEL_CLOZE
from aqt import mw, utils

import os
import copy
import hashlib
import time
import shutil


from PyQt4 import QtGui

def notes_added_message(nrOfNotes):
    if nrOfNotes == 1:
        msg = "<b>1 note</b> and <b>1 card</b> were added to your collection"
    else:
        msg = "<b>1 note</b> and <b>%s cards</b> were added to your collection" % nrOfNotes
    return msg


def rm_media_dir(media_dir):
    for f in os.listdir(media_dir):
        try: os.remove(os.path.join(media_dir, f))
        except: pass
    try: os.rmdir(media_dir)
    except: pass

IMAGE_QA_MODEL_NAME = "Image Q/A - 2.1"
IMAGES_FIELD_NAME = "Images"
SVG_FIELD_NAME = "SVG"
ORIGINAL_IMAGE_FIELD_NAME = "Original Image"
HEADER_FIELD_NAME = "Header"
FOOTER_FIELD_NAME = "Footer"

HEADER_FIELD_IDX = 3 # index starts at zero

css = """\
.card {
  font-family: arial;
  font-size: 20px;
  text-align: center;
  color: black;
  background-color: white;
}

.cloze {}

.cloak {
  line-height: 0; 
  font-size: 0px;
  color: transparent;
  letter-spacing: -1;
}

.cloak > .wizard {
  display: none;
}

.cloak > .cloze > .wizard {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}
"""

WIZARD = """\
<span class="wizard">%s
  <div style="position:relative; width:100%%">
    <div style="position:absolute; top:0; width:100%%">%s</div>
    <div style="position:absolute; top:0; width:100%%">%s%s</div>
  </div>
</span>
""".replace('\n', '') # anki doesn't deal well with newlines inside clozes

### Templates for question and answer
## ImageQA_qfmt == ImageQA_afmt
ImageQA_qfmt = """\
<span class="cloak">
{{cloze:Images}}
</span>
<span style="display:none">{{%s}}</span>
""" % SVG_FIELD_NAME

ImageQA_afmt = """\
<span class="cloak">
{{cloze:Images}}
</span>
"""


def cloze(i, q, a):
    return "{{c%s::[%s]::%s}}" % ((i+1), a, q)

def wizard(svg, bitmap, header, footer):
    if header: _header = header + "<br/>"
    else: _header = ""
    
    if footer: _footer = "<br/><br/><br/>" + footer
    else: _footer = ""
    
    return WIZARD % (header, bitmap, svg, _footer)

def cloak(s):
    return '<span class="cloak">%s</span>' % s

def make_images_field(svgs_q, svgs_a, bitmap, header, footer):
    clozes = [cloze(i,
                    wizard(svgs_q[i], bitmap, header, footer),
                    wizard(svgs_a[i], bitmap, header, footer))
              for i in xrange(len(svgs_q))]
    return "\n".join(clozes)

def add_image_QA_model(col):
    mm = col.models
    m = mm.new(IMAGE_QA_MODEL_NAME)
    m['type'] = MODEL_CLOZE
    m['css'] = css
    # Define the new Fields
    images_field = mm.newField(IMAGES_FIELD_NAME)
    svg_field = mm.newField(SVG_FIELD_NAME)
    original_image_field = mm.newField(ORIGINAL_IMAGE_FIELD_NAME)
    header_field = mm.newField(HEADER_FIELD_NAME)
    footer_field = mm.newField(FOOTER_FIELD_NAME)
    # Add fields:
    mm.addField(m, images_field)
    mm.addField(m, svg_field)
    mm.addField(m, original_image_field)
    mm.addField(m, header_field)
    mm.addField(m, footer_field)
    # Add the new fields to the model
    mm.setSortIdx(m, HEADER_FIELD_IDX)
    # Add template   
    t = mm.newTemplate("Image Q/A")
    t['qfmt'] = ImageQA_qfmt
    t['afmt'] = ImageQA_afmt
    mm.addTemplate(m, t)
    mm.add(m)
    return m

###############################################################
def gen_uniq():
    uniq = hashlib.sha1(str(time.clock())).hexdigest()
    return uniq

def new_bnames(col, media_dir, original_fname):
    shutil.copy(original_fname,
                os.path.join(media_dir, os.path.basename(original_fname)))
    
    d = {}
    uniq_prefix = gen_uniq() + "_"
    
    bnames = os.listdir(media_dir)
    for bname in bnames:
        hash_bname = uniq_prefix + bname
        os.rename(os.path.join(media_dir, bname),
                  os.path.join(media_dir, hash_bname))
        d[bname] = col.media.addFile(os.path.join(media_dir, hash_bname))
    return d

def fname2img(fname):
    return '<img src="' + fname + '" />'


def add_QA_note(col, fnames_q, fnames_a, tags, media_dir, svg_fname,
                 fname_original, header, footer, did):
    
    d = new_bnames(col, media_dir, fname_original)
    
    svgs_q = [fname2img(d[os.path.basename(fname)]) for fname in fnames_q]
    svgs_a = [fname2img(d[os.path.basename(fname)]) for fname in fnames_a]
    svg = fname2img(svg_fname)
    bitmap = fname2img(d[os.path.basename(fname_original)])
    
    m = col.models.byName(IMAGE_QA_MODEL_NAME)
    m['did'] = did
    n = notes.Note(col, model=m)
    
    n.fields = [make_images_field(svgs_q, svgs_a, bitmap, header, footer), # Images
                svg, # SVG
                bitmap, # Original Image (bitmap)
                header, # Header
                footer] # Footer
    
    for tag in tags:
        n.addTag(tag)

    col.addNote(n)
    
    return len(fnames_q)

# Updates the GUI and shows a tooltip
def gui_add_QA_note(fnames_q, fnames_a, media_dir, tags, svg_fname,
                     fname_original, header, footer, did):
    col = mw.col
    mm = col.models
    if not mm.byName(IMAGE_QA_MODEL_NAME): # first time addon is run
        add_image_QA_model(col)
    m = mm.byName(IMAGE_QA_MODEL_NAME)
        
    nrOfNotes = add_QA_note(col, fnames_q, fnames_a,
                            tags, media_dir, svg_fname,
                            fname_original, header, footer, did)
    rm_media_dir(media_dir) # removes the media and the directory
    
    #  We must update the GUI so that the user knows that cards have
    # been added.  When the GUI is updated, the number of new cards
    # changes, and it provides the feedback we want.
    # If we want more feedback, we can add a tooltip that tells the
    # user how many cards have been added.
    # The way to update the GUI will depend on the state
    # of the main window. There are four states (from what I understand):
    #  - "review"
    #  - "overview"
    #  - "deckBrowser"
    #  - "resetRequired" (we will treat this one like "deckBrowser)
    if mw.state == "review":
        mw.reviewer.show()
    elif mw.state == "overview":
        mw.overview.refresh()
    else:
        mw.deckBrowser.refresh() # this shows the browser even if the
          # main window is in state "resetRequired", which in my
          # opinion is a good thing
    utils.tooltip(notes_added_message(nrOfNotes))
