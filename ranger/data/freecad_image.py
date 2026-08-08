#!/usr/bin/python

import sys
sys.path.append('/usr/lib/freecad/lib/')
from pathlib import Path

import FreeCAD
import FreeCADGui as Gui
import Part, Mesh

_, dimensions, path_out, path_in = sys.argv
path_in = Path(path_in)

Gui.showMainWindow()
window = Gui.getMainWindow()
window.showMinimized()

if path_in.suffix.lower() == '.obj':
    Mesh.open(str(path_in))
else:
    Part.open(str(path_in))

x, y = (int(n) for n in dimensions.split(','))

Gui.SendMsgToActiveView('OrthographicCamera')
Gui.SendMsgToActiveView('ViewAxo')

# for f in [,'ViewFront','ViewTop']:

Gui.ActiveDocument.ActiveView.saveImage(path_out, x, y, 'Transparent')

FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
