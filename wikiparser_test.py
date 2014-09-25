import unittest
from wikiparser import *
import os

class TestParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.wikitext = {}
        with open('wikitext_example', 'r', encoding='utf-8') as f:
            cls.wikitext['full'] = f.readline()
            cls.wikitext['lang'] = f.readline()
            cls.wikitext['pron'] = f.readline()
            cls.wikitext['ipa'] = f.readline()

    def test_xml_to_wikitext(self):
        test_xml_file = 'test/small.xml'
        test_out = 'test/test.tmp'
        words_found = parse_xml_to_json(test_xml_file, test_out)
        os.remove(test_out)
        words_expected = 19
        self.assertEqual(words_found, words_expected)

    def test_extract_language_section(self):
        pass

    def test_extract_pronunciation_section(self):
        pass

    def test_extract_ipa(self):
        pass

if __name__ == '__main__':
    unittest.main()
