from wikiparser import *
import unittest
import os
import json

class TestParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """set up wikitext examples with expected output for each parser step.
        examples -- dictionary of word: text, where text is a dictionary
        text['text'] -- full wikitext
        text['lang'] -- only the language section
        text['pron'] -- only the pronunciation section of the language section
        text['ipa'] -- only the extracted ipa
        """
        # cls.examples = [{'word': 'foo', 'text': ... }, {'word': ...]
        with open('test/wikitext_examples.json', 'r', encoding='utf-8') as f:
            cls.examples = json.load(f)

    @unittest.skip('will not be using until refactor or next data dump')
    def test_xml_to_wikitext(self):
        test_xml_file = 'test/small.xml'
        test_out = 'test/test.tmp'
        words_found = parse_xml_to_json(test_xml_file, test_out)
        os.remove(test_out)
        words_expected = 19
        self.assertEqual(words_found, words_expected)

    def test_extract_language_section(self):
        for word, text in self.examples.items():
            if 'text' in text and 'lang' in text:
                comment = text['comment'] if 'comment' in text else None
                with self.subTest(word=word, comment=comment):
                    english = get_english(text['text'])
                    # assert fail on length first, since string output is long
                    self.assertEqual(len(english), len(text['lang']))
                    self.assertEqual(english, text['lang'])

    def test_extract_pronunciation_section(self):
        for word, text in self.examples.items():
            if 'lang' in text and 'pron' in text:
                comment = text['comment'] if 'comment' in text else None
                with self.subTest(word=word, comment=comment):
                    pron = get_pronunciation(text['lang'])
                    self.assertEqual(pron, text['pron'])

    def test_extract_ipa(self):
        for word, text in self.examples.items():
            if 'pron' in text and 'ipa' in text:
                comment = text['comment'] if 'comment' in text else None
                with self.subTest(word=word, comment=comment):
                    ipa = get_ipa(text['pron'])
                    self.assertEqual(sorted(ipa), sorted(text['ipa']))
        # word: hoping

        # using lenient matching for everything within /slashes/: r'/[^/]+/'
        # from full english wordlist: 32028 potential ipa, 12806 without
        pronunciation = json_load('s3_pronunciation.json')

        ipa, _ = map_filter_dict(get_ipa, pronunciation)
        ipa_lenient, _ = map_filter_dict(get_ipa_lenient, pronunciation)
        diff = diff_dict(ipa_lenient, ipa)
        self.assertEqual(len(diff), 247)


        ## future possibility: match [brackets] for phonetic transcriptions
        ## as opposed to just the phonemic transcriptions within /slashes/
        # with self.subTest(word='accend'):
        #     pron = ("===Pronunciation===\n"
        #             "* {{IPA|[\u00e6k\u02c8s\u025bnd]|lang=en}}\n\n")
        #     ipa = "[[\u00e6k\u02c8s\u025bnd]]"
        #     self.assertEqual(get_ipa(pron), ipa)


if __name__ == '__main__':
    unittest.main()
