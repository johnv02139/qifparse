# -*- coding: utf-8 -*-
import unittest
import os
from qifparse.parser import QifParser

filename = os.path.join(os.path.dirname(__file__), 'file.qif')
filename2 = os.path.join(os.path.dirname(__file__), 'transactions_only.qif')
filename3 = os.path.join(os.path.dirname(__file__), 'usw.qif')

def stripAllLines(txt):
    return "\n".join(map(lambda x:x.strip(), txt.splitlines())) + "\n"

class TestQIFParsing(unittest.TestCase):

    # This test simply reads in the file and asserts that an object is created
    # from it, with no exceptions.
    def testParseFile(self):
        qif = QifParser.parse(open(filename, 'U'), '%d/%m/%Y')
        self.assertTrue(qif)

    # The "testWrite" tests verify that we can read text from a QIF file, and
    # then recreate it, virtually identically, from the internal data structures
    # created.  If we're able to do that, we can feel pretty confident that we
    # captured all the relevant data from the file.  At the same time, being
    # able to recreate a QIF file exactly is neither necessary nor sufficient
    # to saying that we've actually understood what the data means.
    #
    # I say "virtually identical" because we use the stripAllLines function,
    # defined above, to create a version of the input that has no superfluous
    # whitespace at the end of lines.  (The alternative would be to make the
    # qif class retain the whitespace, which would be silly.)  Also, by virtue
    # of the 'U' flag given to open, we are able to ignore newlines, and
    # effectively create a version of the file with Unix-style newlines (by
    # rejoining the individual lines with '\n'), which is what we compare with
    # our output.
    def testWriteFile(self):
        data = open(filename, 'U').read()
        qif = QifParser.parse(open(filename, 'U'), '%d/%m/%Y')
        stripped = stripAllLines(data)
# If the strings are not equal, it could be useful to use the "diff" tool from
# the shell to compare them.  The lines below would write out the parsed data to
# a file, which could then be diffed.  But it's not necessary or useful when
# running in an automated way.
#        out = open('out.qif', 'w')
#        out.write(str(qif))
#        out.close()
        self.assertEquals(stripped, str(qif))

    def testWriteWindowsUsaFile(self):
        data = open(filename3, 'U').read()
        qif = QifParser.parse(open(filename3, 'U'), '%m/%d/%Y')
        stripped = stripAllLines(data)
        self.assertEquals(stripped, str(qif))

    def testWriteTransactionsFile(self):
        data = open(filename2, 'U').read()
        qif = QifParser.parse(open(filename2, 'U'), '%d/%m/%Y')
        stripped = stripAllLines(data)
        self.assertEquals(stripped, str(qif))

if __name__ == "__main__":
    import unittest
    unittest.main()
