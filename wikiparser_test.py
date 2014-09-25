from wikiparser import *
import unittest
import os
import json

class TestParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """set up wikitext examples with expected output for each parser step
        wikitext['word']
        wikitext['text'] -- full wikitext
        wikitext['lang'] -- only the language section
        wikitext['pron'] -- only the pronunciation section of the language
                            section
        wikitext['ipa'] -- only the extracted ipa
        """
        cls.wikitext = {}
        with open('test/wikitext_example.json', 'r', encoding='utf-8') as f:
            cls.wikitext = json.load(f)[0]

    def test_xml_to_wikitext(self):
        test_xml_file = 'test/small.xml'
        test_out = 'test/test.tmp'
        words_found = parse_xml_to_json(test_xml_file, test_out)
        os.remove(test_out)
        words_expected = 19
        self.assertEqual(words_found, words_expected)

    def test_extract_language_section(self):
        english_section = get_english_section(self.wikitext['text'])
        # assertion to fail on length first, as the string output is long
        self.assertEqual(len(english_section), len(self.wikitext['lang']))
        self.assertEqual(english_section, self.wikitext['lang'])

    def test_extract_pronunciation_section(self):
        pass

    def test_extract_ipa(self):
        pass

if __name__ == '__main__':
    unittest.main()
