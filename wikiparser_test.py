from wikiparser import *
import unittest
import os
import json

class TestParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """set up wikitext examples with expected output for each parser step
        example['word']
        example['text'] -- full wikitext
        example['lang'] -- only the language section
        example['pron'] -- only the pronunciation section of the language
                            section
        example['ipa'] -- only the extracted ipa
        """
        # cls.examples = [{'word': 'foo', 'text': ... }, {'word': ...]
        with open('test/wikitext_examples.json', 'r', encoding='utf-8') as f:
            cls.examples = json.load(f)

    @unittest.skip('will not be using for a while')
    def test_xml_to_wikitext(self):
        test_xml_file = 'test/small.xml'
        test_out = 'test/test.tmp'
        words_found = parse_xml_to_json(test_xml_file, test_out)
        os.remove(test_out)
        words_expected = 19
        self.assertEqual(words_found, words_expected)

    def test_extract_language_section(self):
        for example in self.examples:
            with self.subTest(word=example['word']):
                english = get_english(example['text'])
                # assert to fail on length first, as the string output is long
                self.assertEqual(len(english), len(example['lang']))
                self.assertEqual(english, example['lang'])

    def test_extract_pronunciation_section(self):
        for example in self.examples:
            with self.subTest(word=example['word']):
                pron = get_pronunciation(example['lang'])
                self.assertEqual(pron, example['pron'])

    def test_extract_ipa(self):
        # from full english wordlist: 32028 with ipa, 12806 without
        for example in self.examples:
            with self.subTest(word=example['word']):
                ipa = get_ipa(example['pron'])
                self.assertEqual(sorted(ipa), sorted(example['ipa']))

        ## future possibility: match [brackets] for phonetic transcriptions
        ## as opposed to just the phonemic transcriptions within /slashes/
        # with self.subTest(word='accend'):
        #     pron = ("===Pronunciation===\n"
        #             "* {{IPA|[\u00e6k\u02c8s\u025bnd]|lang=en}}\n\n")
        #     ipa = "[[\u00e6k\u02c8s\u025bnd]]"
        #     self.assertEqual(get_ipa(pron), ipa)


if __name__ == '__main__':
    unittest.main()
