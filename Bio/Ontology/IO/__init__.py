# Copyright 2013 by Kamil Koziara. All rights reserved.               
# This code is part of the Biopython distribution and governed by its    
# license.  Please see the LICENSE file that should have been included   
# as part of this package.

from Bio.File import as_handle

import OboIO
import GoaIO
import GraphIO
import PrettyIO

_FormatToIterator = { "obo" : OboIO.OboIterator,
                      "tsv" : GoaIO.TsvIterator,
                      "gaf" : GoaIO.GafIterator }

_FormatToWriter = {"obo" : OboIO.OboWriter,
                   "gml" : GraphIO.GmlWriter}

_FormatToPrinter = {"gml" : PrettyIO.GmlPrinter,
                    "png" : PrettyIO.GraphVizPrinter,
                    "txt" : PrettyIO.TxtPrinter,
                    "html": PrettyIO.HtmlPrinter}

def write(data, handle, file_format, version = None):
    """
    Write an ontology data to file.

    Parameters:
     - data - data to write to a file,
     - handle - File handle object to write to, or filename as string
                   (note older versions of Biopython only took a handle),
     - file_format - lower case string describing the file format to write,
         Formats:
             - obo
             - gml
     - version - file format version .
     
    You should close the handle after calling this function.

    """
    
    if not isinstance(file_format, basestring):
        raise TypeError("Need a string for the file format (lower case)")
    if not file_format:
        raise ValueError("Format required (lower case string)")

    with as_handle(handle, 'w') as fp:
        #Map the file format to a writer class
        if file_format in _FormatToWriter:
            writer_class = _FormatToWriter[file_format]
            writer_class(fp).write_file(data, version)
        else:
            raise ValueError("Unknown format '%s'" % file_format)

def parse(handle, file_format):
    """
    Iterate over a gene ontology file.
    
    Parameters:
     - handle - File handle object to read from, or filename as a string,
     - file_format - lower case string describing the file format to write,
         Formats:
             - obo
             - tsv
             - gaf
    """

    if not isinstance(file_format, basestring):
        raise TypeError("Need a string for the file format (lower case)")
    if not file_format:
        raise ValueError("Format required (lower case string)")          
    if file_format != file_format.lower():
        raise ValueError("Format string '%s' should be lower case" % format)
    with as_handle(handle, 'rU') as fp:
        if file_format in _FormatToIterator:
            iterator_generator = _FormatToIterator[file_format]
            it = iterator_generator(fp)

            for el in it:
                yield el
        else:
            raise ValueError("Unknown format '%s'" % file_format)

def pretty_print(enrichment, graph, handle, file_format, params = None):
    """
    Print results returned by enrichment finder in a specified format.
    
     Parameters:
     - enrichment - result from EnrichmentFinder
     - graph - OntologyGraph with containing enriched nodes
     - handle - File handle object to read from, or filename as a string,
     - file_format - lower case string describing the file format to write,
         Formats:
             - gml
             - png
             
    You should close the handle after calling this function.
    """
    
    if not isinstance(file_format, basestring):
        raise TypeError("Need a string for the file format (lower case)")
    if not file_format:
        raise ValueError("Format required (lower case string)")

    with as_handle(handle, 'w') as fp:
        #Map the file format to a writer class
        if file_format in _FormatToPrinter:
            writer_class = _FormatToPrinter[file_format]
            if params == None:
                writer = writer_class(fp)
            else:
                writer = writer_class(fp, params)
            writer.pretty_print(enrichment, graph)
        else:
            raise ValueError("Unknown format '%s'" % file_format)