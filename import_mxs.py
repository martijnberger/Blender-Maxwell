import sys
import os
import time
import bpy
import mathutils

from bpy_extras.io_utils import unpack_list, unpack_face_list
from bpy_extras.image_utils import load_image

from pymaxwell import pymaxwell;

def load(operator, context, filepath):

    print('\nimporting mxs %r' % filepath)

    filepath = os.fsencode(filepath)

    time_main = time.time()
    
    mxs_scene = Cmaxwell(mwcallback)
    
    ok = mxs_scene.readMXS(str(filepath))
    if ok == 0:
        print('\nError reading input file: %r' % (filepath))
    
    time_new = time.time()
    print('\nDone parsing mxs %r in %.4f sec.' % (filepath, (time_new - time_main)))

    time_new = time.time()
    print('finished importing: %r in %.4f sec.' % (filepath, (time_new - time_main)))
    return {'FINISHED'}



