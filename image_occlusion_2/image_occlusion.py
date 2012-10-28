# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, QtWebKit
from aqt import mw, utils, webview
from aqt.qt import *
from anki import hooks

#import urllib
import os
import base64
import tempfile
import socket
import sys

def addons_folder(): return mw.pm.addonFolder() 


import etree.ElementTree as etree

import svgutils
import notes_from_svg


image_occlusion_help_link = "file:///" +\
    os.path.join(addons_folder(),
                 'image_occlusion_2',
                 'help',
                 'Image Occlusion 2.0 - Help page.html')

svg_edit_dir = os.path.join(addons_folder(),
                             'image_occlusion_2',
                             'svg-edit-2.5.1')

ext_image_occlusion_js_path = os.path.join(svg_edit_dir,
                                           'extensions',
                                           'ext-image-occlusion.js')

unedited_svg_basename = "-IMAGE-OCCLUSION-SVG-.svg"

unedited_svg_path = os.path.join(svg_edit_dir,
                             'images',
                             unedited_svg_basename)

unedited_svg_url = 'images/' + unedited_svg_basename

svg_edit_path = os.path.join(svg_edit_dir,
                             'svg-editor.html')



svg_edit_url = QtCore.QUrl.fromLocalFile(svg_edit_path)
svg_edit_url_string = svg_edit_url.toString()

#Add all configuration options we know at this point:
svg_edit_url.setQueryItems([('initStroke[opacity]', '0'),
                            ('initStroke[width]', '0'),
                            ('initTool', 'rect'),
                            ('extensions', 'ext-image-occlusion.js')])

FILE_DIALOG_MESSAGE = "Choose Image"
FILE_DIALOG_FILTER = "Image Files (*.png *jpg *.jpeg *.gif)"

default_conf = {'initFill[color]': 'FFFFFF',
                'mask_fill_color': 'FF0000'}

class ImageOcc_Add(QtCore.QObject):
    def __init__(self, ed):
        super(QtCore.QObject, self).__init__()
        self.ed = ed
        self.mw = mw
        if not 'image_occlusion_conf' in mw.col.conf:
            self.mw.col.conf['image_occlusion_conf'] = default_conf
    
    
    def add_notes(self):
        clip = QApplication.clipboard()
        if clip.mimeData().imageData():
            handle, image_path = tempfile.mkstemp(suffix='.png')
            clip.image().save(image_path)
            self.call_svg_edit(image_path)
            clip.clear()
        
        else:
            image_path = QtGui.QFileDialog.getOpenFileName(None, # parent
                                                       FILE_DIALOG_MESSAGE,
                                                       os.path.expanduser('~'),
                                                       FILE_DIALOG_FILTER)
            if image_path:
                self.call_svg_edit(image_path)
        
        
    def call_svg_edit(self, path):
        d = svgutils.image2svg(path)
        svg = d['svg']
        svg_b64 = d['svg_b64']
        height = d['height']
        width = d['width']

                                
        try:
            self.mw.svg_edit is not None
            select_rect_tool = "svgCanvas.setMode('rect'); "
            set_svg_content = 'svg_content = \'%s\'; ' % svg.replace('\n','')
            set_canvas = 'svgCanvas.setSvgString(svg_content);'
            
            command = select_rect_tool + set_svg_content + set_canvas
            
            self.mw.svg_edit.eval(command)
        
        except:
            
            initFill_color = mw.col.conf['image_occlusion_conf']['initFill[color]']
            url = svg_edit_url
            url.addQueryItem('initFill[color]', initFill_color)
            url.addQueryItem('dimensions', '{0},{1}'.format(width,height))
            url.addQueryItem('source', svg_b64)
            
            self.mw.svg_edit = webview.AnkiWebView()
            
            def onLoadFinished(result):
                if result:
                    self.mw.svg_edit.show()
            
            self.mw.svg_edit.connect(self.mw.svg_edit, QtCore.SIGNAL("loadFinished(bool)"), onLoadFinished)
            self.mw.svg_edit.page().mainFrame().addToJavaScriptWindowObject("pyObj", self)
            self.mw.svg_edit.load(url)

    
    @QtCore.pyqtSlot(str)
    def add_notes_non_overlapping(self, svg_contents):
        svg = etree.fromstring(svg_contents)
        # Get the mask color from mw.col.conf:
        mask_fill_color = mw.col.conf['image_occlusion_conf']['mask_fill_color']
        # Get tags:
        tags = self.ed.note.tags
        # Add notes to the current deck of the collection:
        notes_from_svg.add_notes_non_overlapping(svg, mask_fill_color, tags)
    
    @QtCore.pyqtSlot(str)
    def add_notes_overlapping(self, svg_contents):
        svg = etree.fromstring(svg_contents)
        # Get the mask color from mw.col.conf:
        mask_fill_color = mw.col.conf['image_occlusion_conf']['mask_fill_color']
        # Get tags:
        tags = self.ed.note.tags
        # Add notes to the current deck of the collection:
        notes_from_svg.add_notes_overlapping(svg, mask_fill_color, tags)

def add_image_occlusion_button(ed):
    ed.image_occlusion = ImageOcc_Add(ed)
    ed._addButton("image_occlusion", ed.image_occlusion.add_notes,
            key="Alt+o", size=False, text=_("Image Occlusion"),
            native=True, canDisable=False)

class ImageOcc_Options(QtGui.QWidget):
    def __init__(self, mw):
        super(ImageOcc_Options, self).__init__()
        self.mw = mw
    
    def getNewMaskColor(self):
        # Remove the # sign from QColor.name():
        choose_color_dialog = QColorDialog()
        color = choose_color_dialog.getColor()
        if color.isValid():
            color_ = color.name()[1:]
            self.mw.col.conf['image_occlusion_conf']['mask_fill_color'] = color_
    
    def getNewInitFillColor(self):
        # Remove the # sign from QColor.name():
        choose_color_dialog = QColorDialog()
        color = choose_color_dialog.getColor()
        if color.isValid():
            color_ = color.name()[1:]
            self.mw.col.conf['image_occlusion_conf']['initFill[color]'] = color_
        
    def setupUi(self):
        
        ### Mask color for questions:
        mask_color_label = QLabel('<b>Mask color</b><br>in question')
        
        mask_color_button = QPushButton(u"Choose Color ▾")
        
        mask_color_button.connect(mask_color_button,
                                  SIGNAL("clicked()"),
                                  self.getNewMaskColor)
        ### Initial rectangle color:
        initFill_label = QLabel('<b>Initial color</b><br>for rectangle')
        
        initFill_button = QPushButton(u"Choose Color ▾")
        
        initFill_button.connect(initFill_button,
                                SIGNAL("clicked()"),
                                self.getNewInitFillColor)
        
        
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
        
        # 1st row:
        grid.addWidget(mask_color_label, 0, 0)
        grid.addWidget(mask_color_button, 0, 1)
        # 2nd row:
        grid.addWidget(initFill_label, 1, 0)
        grid.addWidget(initFill_button, 1, 1)
        
        
        self.setLayout(grid) 
        
        self.setWindowTitle('Image Occlusion 2.0 (options)')    
        self.show()

def invoke_ImageOcc_help():
    utils.openLink(image_occlusion_help_link)

mw.ImageOcc_Options = ImageOcc_Options(mw)

options_action = QAction("Image Occlusion 2.0 (options)", mw)
help_action = QAction("Image Occlusion 2.0 (help)", mw)

mw.connect(options_action,
           SIGNAL("triggered()"),
           mw.ImageOcc_Options.setupUi)

mw.connect(help_action,
           SIGNAL("triggered()"),
           invoke_ImageOcc_help) 

mw.form.menuTools.addAction(options_action)
mw.form.menuHelp.addAction(help_action)
    
hooks.addHook('setupEditorButtons', add_image_occlusion_button)


