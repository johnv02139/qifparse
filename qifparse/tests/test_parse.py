# -*- coding: utf-8 -*-
import unittest
import os
from qifparse.parser import QifParser

filename = os.path.join(os.path.dirname(__file__), 'file.qif')
filename2 = os.path.join(os.path.dirname(__file__), 'transactions_only.qif')

def stripAllLines(txt):
    return "\n".join(map(lambda x:x.strip(), txt.splitlines())) + "\n"

class TestQIFParsing(unittest.TestCase):

    def testParseFile(self):
        qif = QifParser.parse(open(filename, 'U'), '%d/%m/%Y')
        self.assertTrue(qif)

    def testWriteFile(self):
        data = open(filename, 'U').read()
        qif = QifParser.parse(open(filename, 'U'), '%d/%m/%Y')
        stripped = stripAllLines(data)
#        out = open('out.qif', 'w')
#        out.write(str(qif))
#        out.close()
        self.assertEquals(stripped, str(qif))

    def testParseTransactionsFile(self):
        data = open(filename2, 'U').read()
        qif = QifParser.parse(open(filename2, 'U'), '%d/%m/%Y')
        stripped = stripAllLines(data)
#        out = open('out.qif', 'w')
#        out.write(str(qif))
#        out.close()
        self.assertEquals(stripped, str(qif))

if __name__ == "__main__":
    import unittest
    unittest.main()
