import etree.ElementTree as etree

from anki import notes, consts
from aqt import mw, utils

import os
import copy

from PyQt4 import QtGui

def notes_added_message(nrOfNotes):
    if nrOfNotes == 1:
        msg = "<b>1 note</b> was added to your collection"
    else:
        msg = "<b>{0} notes</b> were added to your collection".format(nrOfNotes)
    return msg


def rm_media_dir(media_dir):
    for f in os.listdir(media_dir):
        try: os.remove(os.path.join(media_dir, f))
        except: pass
    try: os.rmdir(media_dir)
    except: pass

#def get_as_attribs(d, elt):
#    map = {}
#    for key in d.keys():
#        value = elt.find(key)
#        if value is not None:
#            map[key] = d[key](value)
#    return map

#def add_models(col, models):
#    nrOfModels = 0
#    for model in models.findall('model'):
#        m = col.models.byName(model.find('name').text)
#        if m is None:
#            m = add_model(col, model)
#            nrOfModels += 1
#    return nrOfModels

IMAGE_QA_MODEL_NAME = "Image Q/A - 2.0"
QUESTION_FIELD_NAME = "Question"
ANSWER_FIELD_NAME = "Answer"
SVG_FIELD_NAME = "SVG"
# If QWebView decides to display SVGs with linked PNGs this will be useful:
ORIGINAL_IMAGE_FIELD_NAME = "Original Image"

image_QA_qfmt = '<center>{{%(q)s}}<span style="display:none">{{%(svg)s}} {{%(im)s}}</span></center>' % \
    {'q': QUESTION_FIELD_NAME, 'svg': SVG_FIELD_NAME, 'im': ORIGINAL_IMAGE_FIELD_NAME}

image_QA_afmt = '<center>{{%(a)s}}</center>' % {'a': ANSWER_FIELD_NAME}

def add_image_QA_model(col):
    mm = col.models
    m = mm.new(IMAGE_QA_MODEL_NAME)
    # Add fields:
    question_field = mm.newField(QUESTION_FIELD_NAME)
    mm.addField(m, question_field)
    answer_field = mm.newField(ANSWER_FIELD_NAME)
    mm.addField(m, answer_field)
    svg_field = mm.newField(SVG_FIELD_NAME)
    mm.addField(m, svg_field)
    original_image_field = mm.newField(ORIGINAL_IMAGE_FIELD_NAME)
    mm.addField(m, original_image_field)
    # Add template   
    t = mm.newTemplate("Image Q/A")
    t['qfmt'] = image_QA_qfmt
    t['afmt'] = image_QA_afmt
    mm.addTemplate(m, t)
    mm.add(m)
    return m
###############################################################
def new_bnames(col, media_dir):
    bnames = os.listdir(media_dir)
    d = {}
    for bname in bnames:
        d[bname] = col.media.addFile(os.path.join(media_dir, bname))
    return d

def fname2img(fname):
    return '<img src="' + fname + '" />'

def add_QA_note(col, fname_q, fname_a, tags, fname_svg):
    model_name = IMAGE_QA_MODEL_NAME
    
    m = col.models.byName(model_name)
    m['did'] = col.conf['curDeck']

    n = notes.Note(col, model=m)
    n.did = col.conf['curDeck']
    n.fields = [fname2img(fname_q), fname2img(fname_a), fname2img(fname_svg), ""]
    
    for tag in tags:
        n.addTag(tag)

    col.addNote(n)
    
    return n

def add_QA_notes(col, fnames_q, fnames_a, tags, media_dir, svg_fname):
    d = new_bnames(col, media_dir)
    nrOfNotes = 0
    for (q,a) in zip(fnames_q, fnames_a):
        add_QA_note(col,
                    d[os.path.basename(q)],
                    d[os.path.basename(a)],
                    tags,
                    d[os.path.basename(svg_fname)])
        nrOfNotes += 1
    return nrOfNotes

# Updates the GUI and shows a tooltip
def gui_add_QA_notes(fnames_q, fnames_a, media_dir, tags, svg_fname):
    col = mw.col
    mm = col.models
    if not mm.byName(IMAGE_QA_MODEL_NAME):
        add_image_QA_model(col)
    nrOfNotes = add_QA_notes(col, fnames_q, fnames_a, tags, media_dir, svg_fname)
    rm_media_dir(media_dir) # removes the media and the directory      
    mw.deckBrowser.show()
    utils.tooltip(notes_added_message(nrOfNotes))