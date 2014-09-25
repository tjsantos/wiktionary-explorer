import unittest
from wikiparser import *
import os

class TestParser(unittest.TestCase):

    def test_xml_to_wikitext(self):
        test_xml_file = 'small.xml'
        test_out = 'test.tmp'
        words_found = parse_xml_to_json(test_xml_file, test_out)
        os.remove(test_out)
        words_expected = 19
        self.assertEqual(words_found, words_expected)

    def test_extract_wikitext_section(self):
        pass

    def test_extract_ipa(self):
        pass

if __name__ == '__main__':
    unittest.main()
