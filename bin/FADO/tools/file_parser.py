#  Copyright 2019-2025, FADO Contributors (cf. AUTHORS.md)
#
#  This file is part of FADO.
#
#  FADO is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  FADO is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with FADO.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np


class LabelReplacer:
    """
    Replaces all occurrences of a text label (passed to __init__) by value.
    Values may be numeric or strings, only the first index of arrays is written.

    See also
    --------
    ArrayLabelReplacer, to write entire arrays.
    """
    def __init__(self,label):
        self._label = label

    def write(self,file,value):
        with open(file) as f:
            lines = f.readlines()

        if isinstance(value,np.ndarray): value = value[0]

        newLines = []
        for line in lines:
            newLines.append(line.replace(self._label,str(value)))
        #end

        with open(file,"w") as f:
            f.writelines(newLines)
     #end
#end


class ArrayLabelReplacer:
    """
    Replaces all occurrences of a text label (passed to __init__) by an iterable value.
    The different entries of value are joined by the delimiter passed to __init__.

    See also
    --------
    LabelReplacer, to write scalar numeric values or text.
    """
    def __init__(self,label,delim=","):
        self._label = label
        self._delim = delim

    def write(self,file,value):
        with open(file) as f:
            lines = f.readlines()

        valueStr = ""
        for v in value:
            valueStr += str(v)+self._delim
        valueStr = valueStr.strip(self._delim)

        newLines = []
        for line in lines:
            newLines.append(line.replace(self._label,valueStr))
        #end

        with open(file,"w") as f:
            f.writelines(newLines)
    #end
#end


class PreStringHandler:
    """
    Read or write "delim"-separated values in front of a label (prefix-string),
    which must start the line. Both label and delimiter are passed to __init__.
    When reading the class can only handle the first occurrence of the label,
    when writing every occurrence will be handled.

    Example
    -------
    X= 1, 2, 3
    PreStringHandler("X=") -> [1, 2, 3]
    """
    def __init__(self,label,delim=","):
        self._label = label
        self._delim = delim

    def read(self,file):
        with open(file) as f:
            lines = f.readlines()

        data = []
        for line in lines:
            if line.startswith(self._label):
                data = line.lstrip(self._label).strip().split(self._delim)
                break
            #end
        if not data:
            raise RuntimeError(self._label + " not found.")

        size = len(data)
        if size==1: return float(data[0])

        value = np.ndarray((size,))
        for i in range(size):
            value[i] = float(data[i])

        return value
    #end

    def write(self,file,value):
        with open(file) as f:
            lines = f.readlines()

        # make scalars iterable
        if isinstance(value,float) or isinstance(value,int):
            value = [value]

        newLine = ""
        for i, line in enumerate(lines):
            if line.startswith(self._label):
                if not newLine:
                    newLine += self._label
                    for val in value:
                        newLine += str(val)+self._delim
                    newLine = newLine[0:-len(self._delim)]+"\n"
                #end
                lines[i] = newLine
            #end
        #end

        with open(file,"w") as f:
            f.writelines(lines)
    #end
#end


class TableReader:
    """
    Reads data (up to 2D arrays) from a table-like file, e.g. CSV.

    Parameters
    ----------
    row     : Row of the table defined by start and end (use None for all rows, -1 for last row).
    col     : Column (same behavior as row).
    start   : Row and column (tuple) of the file defining the top left corner of the table.
    end     : Tuple defining the bottom right corner of the table (use None to capture everything).
    delim   : The delimiter used to separate columns.

    Example
    -------
    col1 col2 col3
    0    1    2
    3    4    5
    >>> TableReader(1,1,(1,1),(None,None)) -> 5
    >>> TableReader(0,None,(1,0),(2,None)) -> [0, 1, 2]
    """
    def __init__(self,row=0,col=0,start=(0,0),end=(None,None),delim=""):
        self._row = row
        self._col = col
        self._end = end
        self._start = start
        self._delim = delim

    def read(self,file):
        with open(file) as f:
            lines = f.readlines()

        # skip header and footer rows
        lines = lines[self._start[0]:self._end[0]]
        numRow = len(lines)

        # process lines
        data = None
        numCol = 0
        for row, line in enumerate(lines):
            for char in self._delim:
                line = line.replace(char," ")

            tmp = line.strip().split()[self._start[1]:self._end[1]]

            if numCol == 0:
                numCol = len(tmp)
                data = np.ndarray((numRow,numCol))
            elif numCol != len(tmp):
                raise RuntimeError("Data is not in table format.")
            #end

            for col in range(numCol):
                data[row,col] = float(tmp[col])
        #end

        if self._row is None:
            if self._col is None:
                return data
            else:
                return data[:,self._col]
            #end
        else:
            if self._col is None:
                return data[self._row,:]
            else:
                return data[self._row,self._col]
            #end
        #end
    #end
#end


class LabeledTableReader(TableReader):
    """
    Reads elements from a column of a table-like file identified by "label".
    The entire file must be in table format, and the label appear on the first row.

    Parameters
    ----------
    label : Title of the column (usually a string).
    delim : Delimiter character separating the columns.
    rang  : Row range, by default return the last value in the column.

    See also
    --------
    TableReader, PreStringHandler
    """
    def __init__(self,label,delim=",",rang=(-1,None)):
        self._label = label
        self._range = rang
        TableReader.__init__(self,None,None,(1,0),(None,None),delim)
    #end

    def read(self,file):
        with open(file) as f:
            header = f.readline().split(self._delim)
        header = [x.strip() for x in header]
        self._col = header.index(self._label)
        data = TableReader.read(self,file)[self._range[0]:self._range[1]]
        if data.size == 1: data = data[0]
        return data
    #end
#end


class TableWriter:
    """
    Writes data (up to 2D arrays) to table-like files.

    Parameters
    ----------
    delim       : Set of characters used to separate the columns of the input data.
    start       : Row column tuple defining the top left corner of the target area in the file.
    end         : Bottom right corner of the target area.
    delimChars  : List of all characters used to separate the columns of the target file.

    See also
    --------
    TableReader (start/end work the same way).
    """
    def __init__(self,delim="  ",start=(0,0),end=(None,None),delimChars=""):
        self._end = end
        self._start = start
        self._delim = delim
        self._delimChars = delimChars

    def write(self,file,values):
        # load file
        with open(file) as f:
            lines = f.readlines()

        # check if the values are remotely compatible with the file
        if len(lines) < values.shape[0]: return # "soft fail"

        # keep top, bottom, left, and right the same
        newLines = lines[0:self._start[0]]
        footerLines = []
        if self._end[0] is not None: footerLines = lines[self._end[0]:]

        # skip header and footer rows
        lines = lines[self._start[0]:self._end[0]]
        if not lines[-1].strip(): lines = lines[0:-1]

        if len(lines) != values.shape[0]:
            raise RuntimeError("Data and file have different number of rows.")
        numCol = values.size/values.shape[0]

        # process lines
        for (line,row) in zip(lines,values):
            for char in self._delimChars:
                line = line.replace(char," ")

            tmp = line.strip().split()

            if numCol != len(tmp[self._start[1]:self._end[1]]):
                raise RuntimeError("Data and file have different number of columns.")
            #end

            # reconstruct left and right parts
            newLine = ""
            for string in tmp[0:self._start[1]]:
                newLine += string+self._delim

            # handle case where row is not iterable
            if values.ndim==1: row=[row]

            for val in row:
                newLine += str(val)+self._delim

            if self._end[1] is not None:
                for string in tmp[self._end[1]:]:
                    newLine += string+self._delim

            newLines.append(newLine.strip()+"\n")
        #end

        # write file
        with open(file,"w") as f:
            f.writelines(newLines)
            f.writelines(footerLines)
    #end
#end

