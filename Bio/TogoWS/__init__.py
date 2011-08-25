# Copyright 2010-2011 by Peter Cock.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

"""Provides code to access the TogoWS integrated websevices of DBCLS, Japan.

This module aims to make the TogoWS (from DBCLS, Japan) easier to use. See:
http://togows.dbcls.jp/

The TogoWS REST service provides simple access to a range of databases, acting
as a proxy to shield you from all the different provider APIs. This works using
simple URLs (which this module will construct for you). For more details, see
http://togows.dbcls.jp/site/en/rest.html

The functionality is somewhat similar to Biopython's Bio.Entrez module which
provides access to the NCBI's Entrez Utilities (E-Utils) which also covers a
wide range of databases.

Currently TogoWS does not provide any usage guidelines (unlike the NCBI whose
requirements are reasonably clear). To avoid risking overloading the service,
Biopython will only allow three calls per second.

The TogoWS SOAP service offers a more complex API for calling web services
(essentially calling remote functions) provided by DDBJ, KEGG and PDBj. For
example, this allows you to run a remote BLAST search at the DDBJ. This is
not yet covered by this module, however there are lots of Python examples
on the TogoWS website using the SOAPpy python library. See:
http://togows.dbcls.jp/site/en/soap.html
http://soapy.sourceforge.net/
"""

import urllib
import time
from Bio import File

#Caches:
_search_db_names = None
_fetch_db_names = None
_fetch_db_fields = {}
_fetch_db_formats = {}

def _get_fields(url):
    """Queries a TogoWS URL for a plain text list of values (PRIVATE)."""
    handle = _open(url)
    fields = handle.read().strip().split()
    handle.close()
    return fields

def _get_entry_dbs():
    return _get_fields("http://togows.dbcls.jp/entry")

def _get_entry_fields(db):
    return _get_fields("http://togows.dbcls.jp/entry/%s?fields" % db)

def _get_entry_formats(db):
    return _get_fields("http://togows.dbcls.jp/entry/%s?formats" % db)

def tfetch(db, id, format=None, field=None):
    """TogoWS fetch entry (returns a handle).

    db - database (string), see list below.
    id - identier (string) or a list of identifiers (either as a list of
         strings or a single string with comma separators).
    format - return data file format (string), options depend on the database
             e.g. "xml", "json", "gff", "fasta", "ttl" (RDF)
    field - specific field from within the database record (string)
            e.g. "au" or "authors" for pubmed.

    At the time of writing, TogoWS website claims it supports the following
    databases:

    KEGG: gene, orthology, enzyme, compound, drug, glycan, reaction
    DDBJ: ddbj, dad
    PDBj: pdb
    NCBI: gene, genome, genomeprj, geo, journals, mesh, nucleotide, omim,
          pmc, protein, pubmed, taxonomy, cdd, popset, snp, unigene,
          homologene, nuccore, nucest, nucgss, unists
    EBI:  biomodels, chebi, ensembl, go, interpro, reactome, uniprot,
          uniparc, uniref100, uniref90, uniref50, msdchem, msdpdb

    However, the list given at http://togows.dbcls.jp/entry/ is much smaller.
        
    The name of this function (tfetch) mimics that of the related NCBI
    Entrez service EFetch, available in Biopython as Bio.Entrez.efetch(...)
    """
    global _fetch_db_names, _fetch_db_fields, fetch_db_formats
    if _fetch_db_names is None:
        _fetch_db_names = _get_entry_dbs()
    if db not in _fetch_db_names:
        raise ValueError("TogoWS entry fetch does not officially support "
                         "database '%s'." % db)
    if field:
        try:
            fields = _fetch_db_fields[db]
        except KeyError:
            fields = _get_entry_fields(db)
            _fetch_db_fields[db] = fields
        if field not in fields:
            #TODO - Make this a ValueError? Right now TogoWS appears to support
            #some undocumented fields like "length" for "embl".
            import warnings
            warnings.warn("TogoWS entry fetch does not explicitly support "
                          "field '%s' for database '%s'." % (field, db))
    if format:
        try:
            formats = _fetch_db_formats[db]
        except KeyError:
            formats = _get_entry_formats(db)
            _fetch_db_fields[db] = formats
        if format not in formats:
            raise ValueError("TogoWS entry fetch does not explicitly support "
                             "format '%s' for database '%s'." % (format, db))

    if isinstance(id, list):
        id = ",".join(id)
    url="http://togows.dbcls.jp/entry/%s/%s" % (db, id)
    if field:
        url += "/" + field
    if format:
        url += "." + format
    return _open(url)

def tsearch_count(db, query):
    """TogoWS search count (returns an integer).

    db - database (string), see http://togows.dbcls.jp/search
    query - search term (string)

    You could then use the count to download a large set of search results in
    batches using the offset and limit options to Bio.TogoWS.tsearch().
    """
    global _search_db_names
    if _search_db_names is None:
        _search_db_names = _get_fields("http://togows.dbcls.jp/search")
    if db not in _search_db_names:
        #TODO - Make this a ValueError? Right now despite the HTML website
        #claiming to, the "gene" or "ncbi-gene" don't work and are not listed.
        import warnings
        warnings.warn("TogoWS search does not officially support database '%s'. "
                      "See http://togows.dbcls.jp/search/ for options." % db)
    #TODO - Encode spaces etc
    handle = _open("http://togows.dbcls.jp/search/%s/%s/count" % (db, query))
    count = int(handle.read().strip())
    handle.close()
    return count

def tsearch_iter(db, query, batch=100):
    """TogoWS search iteratating over the results (generator function).

    db - database (string), see http://togows.dbcls.jp/search
    query - search term (string)
    batch - number of search results to pull back each time talk to TogoWS.

    You would use this function within a for loop, e.g.

    for id in tsearch_iter("pubmed", "lung+cancer+drug"):
        print id #maybe fetch data with tfetch?
    """
    count = tsearch_count(db, query)
    if not count:
        raise StopIteration
    remain = count
    offset = 1 #They don't use zero based counting
    while remain:
        batch = min(batch, remain)
        ids = tsearch(db, query, offset, batch).read().strip().split()
        assert len(ids)==batch, "Got %i, expected %i" % (len(ids), batch)
        #print "offset %i, %s ... %s" % (offset, ids[0], ids[1])
        for identifier in ids:
            yield identifier
        offset += batch
        remain -= batch
    

def tsearch(db, query, offset=None, count=None, format=None):
    """TogoWS search (returns a handle).

    db - database (string), see http://togows.dbcls.jp/search/
    query - search term (string)
    offset, count - optional integers specifying which result to start from
            (1 based) and the number of results to return.
    format - return data file format (string), e.g. "json", "ttl" (RDF)
             By default plain text is returned.

    At the time of writing, TogoWS supports a long list of databases, including
    many from the NCBI (e.g. "ncbi-pubmed" or "pubmed", "ncbi-genbank" or
    "genbank", "ncbi-taxonomy"), EBI (e.g. "ebi-ebml" or "embl", "ebi-uniprot"
    or "uniprot, "ebi-go"), and KEGG (e.g. "kegg-compound" or "compound").
        
    The name of this function (tsearch) mimics that of the related NCBI
    Entrez service ESearch, available in Biopython as Bio.Entrez.esearch(...)

    See also the function Bio.TogoWS.tsearch_count() which returns the number
    of matches found, and the Bio.TogoWS.tsearch_iter() function which allows
    you to iterate over the search results (taking care of batching for you).
    """
    global _search_db_names
    if _search_db_names is None:
        _search_db_names = _get_fields("http://togows.dbcls.jp/search")
    if db not in _search_db_names:
        #TODO - Make this a ValueError? Right now despite the HTML website
        #claiming to, the "gene" or "ncbi-gene" don't work and are not listed.
        import warnings
        warnings.warn("TogoWS search does not explicitly support database '%s'. "
                      "See http://togows.dbcls.jp/search/ for options." % db)
    #TODO - Encode spaces etc
    url="http://togows.dbcls.jp/search/%s/%s" % (db, query)
    if offset is not None and count is not None:
        if offset<=0:
            raise ValueError("Offset should be at least one")
        if count<=0:
            raise ValueError("Count should be at least one")
        url += "/%i,%i" % (offset, count)
    elif offset is not None or count is not None:
        raise ValueError("Expect BOTH offset AND count to be provided (or neither)")
    if format:
        url += "." + format
    #print url
    return _open(url)

def tconvert(data, in_format, out_format):
    """TogoWS convert (returns a handle).
    
    data - string or handle containing input record(s)
    in_format - string describing the input file format (e.g. "genbank")
    out_format - string describing the requested output format (e.g. "fasta")
    
    Note that Biopython has built in support for conversion of sequence and
    alignnent file formats (functions Bio.SeqIO.convert and Bio.AlignIO.convert)
    """
    #TODO - Check the formats are supported
    url="http://togows.dbcls.jp/convert/%s.%s" % (in_format, out_format)
    #TODO - Should we just accept a string not a handle? What about a filename?
    if hasattr(data, "read"):
        #Handle
        return _open(url, post={"data":data.read()})
    else:
        #String
        return _open(url, post={"data":data})

def _open(url, post=None):
    """Helper function to build the URL and open a handle to it (PRIVATE).

    Open a handle to TogoWS. Does some very simple error checking, and will
    raise an IOError if it encounters an error.

    In the absense of clear guidelines, this function also enforces "up to
    three queries per second" to avoid abusing the TogoWS servers.
    """
    delay = 0.333333333 #one third of a second
    current = time.time()
    wait = _open.previous + delay - current
    if wait > 0:
        time.sleep(wait)
        _open.previous = current + wait
    else:
        _open.previous = current

    #print url
    if post:
        handle = urllib.urlopen(url, urllib.urlencode(post))
    else:
        handle = urllib.urlopen(url)

    # Wrap the handle inside an UndoHandle.
    uhandle = File.UndoHandle(handle)

    # Check for errors in the first 10 lines.
    # This is kind of ugly.
    lines = []
    for i in range(10):
        lines.append(uhandle.readline())
    for i in range(9, -1, -1):
        uhandle.saveline(lines[i])
    data = ''.join(lines)

    if data == '':
        #ValueError? This can occur with an invalid formats or fields
        #e.g. http://togows.dbcls.jp/entry/pubmed/16381885.au
        #which is an invalid file format, I meant to try this
        #instead http://togows.dbcls.jp/entry/pubmed/16381885/au
        raise IOError("TogoWS replied with no data:\n%s % url")
    if data == ' ':
        #I've seen this on things which should work, e.g.
        #e.g. http://togows.dbcls.jp/entry/genome/X52960.fasta
        raise IOError("TogoWS replied with just a single space:\n%s" % url)
    if data.startswith("Error: "):
        #TODO - Should this be a value error (in some cases?)
        raise IOError("TogoWS replied with an error message:\n\n%s\n\n%s" \
                      % (data, url))
    if "<title>We're sorry, but something went wrong</title>" in data:
        #ValueError? This can occur with an invalid formats or fields
        raise IOError("TogoWS replied: We're sorry, but something went wrong:\n%s" \
                      % url)
        
    return uhandle

_open.previous = 0


if __name__ == "__main__":

    try:
        _get_fields("http://togows.dbcls.jp/entry/invalid?fields")
        assert False, "Should fail"
    except IOError, e:
        assert "Error: Invalid database." in str(e)
        pass

    print tfetch("pubmed", "16381885", field="au").read()
    print tfetch("pubmed", "16381885", field="authors").read()
    print tfetch("ddbj", "X52960").read()
    print tfetch("ddbj", "X52960", "fasta").read()
    print tfetch("ddbj", "X52960", "gff").read()
    try:
        print tfetch("ddbj", "X52960", "text").read()
    except Exception, e:
        print e
    print tfetch("uniprot", ["A1AG1_HUMAN","A1AG1_MOUSE"]).read()

    """
    names1, names2 = tfetch("pubmed", "16381885,19850725", field="authors").read().strip().split("\n")
    assert names1.split("\t") == ['Kanehisa, M.', 'Goto, S.', 'Hattori, M.', 'Aoki-Kinoshita, K. F.', 'Itoh, M.', 'Kawashima, S.', 'Katayama, T.', 'Araki, M.', 'Hirakawa, M.']
    assert names2.split("\t") == ['Kaminuma, E.', 'Mashima, J.', 'Kodama, Y.', 'Gojobori, T.', 'Ogasawara, O.', 'Okubo, K.', 'Takagi, T.', 'Nakamura, Y.']

    assert tsearch_count("uniprot", "lung+cancer") > 1000
    #print tsearch("uniprot", "lung+cancer").read().strip().split()

    from Bio import SeqIO
    print SeqIO.read(tfetch("ddbj", "X52960", "fasta"), "fasta")
    print SeqIO.read(tfetch("protein", "16130152", "fasta"), "fasta")
    print SeqIO.read(tfetch("protein", "16130152"), "gb")
    """

    #Current count is 1276, so compare all in one to batched:
    #assert list(tsearch_iter("uniprot", "lung+cancer",batch=50)) \
    #    == list(tsearch_iter("uniprot", "lung+cancer",batch=100))
    all_in_one = tsearch("uniprot", "lung+cancer").read().strip().split("\n")
    if len(all_in_one) == 100:
        print "Oh, search was capped at 100."
    else:
        batched = list(tsearch_iter("uniprot", "lung+cancer"))
        assert all_in_one == batched, "All: %s\nBatched: %s" % (all_in_one, batched)
