import tempfile
import copy
import os

from svgutils import *
import add_notes

from aqt import mw
from aqt import utils

import os
import urllib
import time

from PyQt4 import QtGui

def add_notes_non_overlapping(svg, q_color, tags):
    svg = copy.deepcopy(svg)
    color = "#" + q_color
    
    # The number of cards that will be generated.
    nr_of_cards = nr_of_shapes(svg)
    
    # Get a temporary directory to store the images
    media_dir = tempfile.mkdtemp(prefix="media-for-anki")
    
    svg_fname = os.path.join(media_dir, "source_svg.svg")
    f = open(svg_fname, 'w')
    f.write(etree.tostring(svg))
    f.close()
 
    fnames_q_svg = gen_fnames_q(media_dir, nr_of_cards, 'svg')
    fnames_a_svg = gen_fnames_a(media_dir, nr_of_cards, 'svg')
    
    fnames_q_png = gen_fnames_q(media_dir, nr_of_cards, 'png')
    fnames_a_png = gen_fnames_a(media_dir, nr_of_cards, 'png')
    
    # Generate the question sides of the cards:
    for i in xrange(nr_of_cards): 
        #  We use a deep copy because we will be destructively modifying
        # the variable svg_i
        svg_i = copy.deepcopy(svg)
        shapes_layer = svg_i[shapes_layer_index]
        #  We change the color of the current shape, so that the user
        # knows what part of the label he is being asked to name
        ## i+1 because <title> doesn't make a card!
        set_color_recursive(shapes_layer[i+1], color)
        f = open(fnames_q_svg[i], 'w')
        f.write(etree.tostring(svg_i))
        f.close()

    # Generate the answer sides of the cards:
    for i in xrange(nr_of_cards): # <title> doesn't make a card!
        #  We use a deep copy because we will be destructively modifying
        # the variable svg_i
        svg_i = copy.deepcopy(svg)
        shapes_layer = svg_i[shapes_layer_index]
        ## i+1 because <title> doesn't make a card!
        shapes_layer.remove(shapes_layer[i+1])
        f = open(fnames_a_svg[i], 'w')
        f.write(etree.tostring(svg_i))
        f.close()
    
    s = []
    # Convert questions to PNG:
    for q_svg,q_png in zip(fnames_q_svg, fnames_q_png):
        s.append(rasterize_svg(q_svg, q_png))
    # Convert answers to PNG:
    for a_svg,a_png in zip(fnames_a_svg, fnames_a_png):
        s.append(rasterize_svg(a_svg, a_png))
    
    # Just a way to make the program wait... Ugly hack
    QtGui.QMessageBox.information(None, "Info", "Notes generated: " + str(len(s)/2))
    
    # Remove question SVGs
    for q_svg in fnames_q_svg:
        os.remove(q_svg)
    # Remove answer SVGs
    for a_svg in fnames_a_svg:
        os.remove(a_svg)
    
    add_notes.gui_add_QA_notes(fnames_q_png, fnames_a_png, media_dir, tags, svg_fname)
    
    return media_dir

def add_notes_overlapping(svg, q_color, tags):
    svg = copy.deepcopy(svg)
    color = "#" + q_color
    
    # The number of cards that will be generated.
    nr_of_cards = nr_of_shapes(svg)
    
    # Get a temporary directory to store the images
    media_dir = tempfile.mkdtemp(prefix="media-for-anki")
    
    svg_fname = os.path.join(media_dir, "source_svg.svg")
    f = open(svg_fname, 'w')
    f.write(etree.tostring(svg))
    f.close()
 
    fnames_q_svg = gen_fnames_q(media_dir, nr_of_cards, 'svg')
    fname_a_svg = gen_fnames_a(media_dir, 1, 'svg')[0]
    
    fnames_q_png = gen_fnames_q(media_dir, nr_of_cards, 'png')
    fname_a_png = gen_fnames_a(media_dir, 1, 'png')[0]
    
    # Generate the question sides of the cards:
    for i in xrange(nr_of_cards): 
        #  We use a deep copy because we will be destructively modifying
        # the variable svg_i
        svg_i = copy.deepcopy(svg)
        shapes_layer = svg_i[shapes_layer_index]
        shapes = [shapes_layer[j+1] for j in xrange(nr_of_cards)]
        j = 0
        for shape in shapes:
            if j == i:
                set_color_recursive(shape, q_color)
            else:
                shapes_layer.remove(shape)
            j = j+1
                
        f = open(fnames_q_svg[i], 'w')
        f.write(etree.tostring(svg_i))
        f.close()
    
    # Generate the answer side of the cards by deleting all masks
    svg_a = copy.deepcopy(svg)
    shapes_layer = svg_a[shapes_layer_index]
    shapes = [shapes_layer[j+1] for j in xrange(nr_of_cards)]
    for shape in shapes:
        shapes_layer.remove(shape)
    # Generate the answer side of the cards:
    f = open(fname_a_svg, 'w')
    f.write(etree.tostring(svg_a))
    f.close()
    
    s = []
    # Convert questions to PNG:
    for q_svg,q_png in zip(fnames_q_svg, fnames_q_png):
        s.append(rasterize_svg(q_svg, q_png))
    # Convert answers to PNG:
    s.append(rasterize_svg(fname_a_svg, fname_a_png))

    # Just a way to make the program wait... Ugly hack
    QtGui.QMessageBox.information(None, "Info", "Notes generated: " + str(len(s)-1))
    
    for q_svg in fnames_q_svg:
        os.remove(q_svg)
    os.remove(fname_a_svg)
    
    # add notes, updating the GUI:
    add_notes.gui_add_QA_notes(fnames_q_png, [fname_a_png]*nr_of_cards, media_dir, tags, svg_fname)
    
    return media_dir