# Copyright 2013 by Kamil Koziara. All rights reserved.               
# This code is part of the Biopython distribution and governed by its    
# license.  Please see the LICENSE file that should have been included   
# as part of this package.

import unittest
from Bio.Ontology.Data import GeneAnnotation
from Bio.Ontology.IdResolver import FirstOneResolver

class FirstOneResolverTest(unittest.TestCase):


    def test_resolve(self):
        assocs = [GeneAnnotation('FB', 'FBgn0004364', 'x', 'x',
                       ['18wheeler', 'CG8896', 'CT25100'],
                       'x', ['x'], [], '',[]),
                  GeneAnnotation('FB', 'FBgn0043467', 'x', 'x',
                       [],
                       'x', ['x'], [], '',[]),
                  GeneAnnotation('FB', 'FBgn0004907', 'x', 'x',
                       ['14-3-3', '14-3-3 zeta', 'x'],
                       'x', ['x'], [], '',[]),
                  GeneAnnotation('FB', 'FBgn0010339', 'x', 'x',
                       ['CG8340', 'GTP-bp', 'X71866', 'x'],
                       'x', ['x'], [], '',[])
                  ]
        resolver = FirstOneResolver(assocs)
        resolved = [resolver.resolve(x) for x in ['FBgn0043467', 'CT25100',
                                                  'x', 'FBgn0010340']]
        expected = ['FBgn0043467', 'FBgn0004364', 'FBgn0004907', 'FBgn0010340']
        self.assertEqual(expected, resolved)
        
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity = 2)
    unittest.main(testRunner=runner)