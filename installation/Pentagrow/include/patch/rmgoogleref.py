#! /usr/bin/python
#
# Remove links to google fonts from documentation

import sys
import os

def printclean(fin, fout):
    fpin = open(fin, 'r')
    fpout = open(fout, 'w')
    for line in fpin:
        if line.find('fonts.googleapis.com') == -1:
            fpout.write(line)
        else:
            pass

def descend(rootdir):
    for subdir, dirs, files in os.walk(rootdir):
        for ifile in files:
            if ifile.find('.html') != -1:
                print ('Processing file: ',ifile)
                fname = os.path.join(subdir, ifile)
                printclean(fname, 'tmp.html')
                os.remove(fname)
                os.rename('tmp.html', fname)

if __name__ == '__main__':
    for fn in sys.argv[1:]:
        if os.path.isdir(fn):
            descend(fn)
        else:
            printclean(fn, 'tmp.html')
            os.remove(fn)
            os.rename('tmp.html', fn)
        
