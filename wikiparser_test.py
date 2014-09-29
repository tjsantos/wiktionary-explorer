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
        # examples = {'word': {'text': ..., 'lang': ...}, 'word2': {...}}
        cls.examples = json_load('test/wikitext_examples.json')

    @unittest.skip('will not be using until refactor or next data dump')
    def test_xml_to_wikitext(self):
        test_xml_file = 'test/small.xml'
        test_out = 'test/test.tmp'
        words_found = parse_xml_to_json(test_xml_file, test_out)
        os.remove(test_out)
        words_expected = 19
        self.assertEqual(words_found, words_expected)

    def _test_examples_parse_step(self, from_label, to_label):
        """helper method to test specific parse steps"""
        step_names = ['text', 'lang', 'pron', 'ipa']
        self.assertIn(from_label, step_names)
        self.assertIn(to_label, step_names)
        map_functions = {'lang': get_english,
                         'pron': get_pronunciation,
                         'ipa': get_ipa}
        mapper = map_functions[to_label]
        # obtain only the relevant examples for the given parse step
        examples = ((word, text) for word, text in self.examples.items() if
                    from_label in text and to_label in text)
        for word, text in examples:
            comment = text['comment'] if 'comment' in text else None
            with self.subTest(word=word, comment=comment):
                result = mapper(text[from_label])
                expected = text[to_label]
                if from_label == 'text':
                    # full text is long so assert on length first
                    self.assertEqual(len(result), len(expected))
                self.assertEqual(result, expected)

    def test_extract_language_section(self):
        self._test_examples_parse_step('text', 'lang')

    def test_extract_pronunciation_section(self):
        self._test_examples_parse_step('lang', 'pron')

    def test_extract_ipa(self):
        self._test_examples_parse_step('pron', 'ipa')
        # word: hoping

        # using lenient matching for everything within /slashes/: r'/[^/]+/'
        # from full english wordlist: 32028 potential ipa, 12806 without
        pronunciation = json_load('test/s3_pronunciation.json')
        self.assertGreater(len(pronunciation), 44000)

        ipa, _ = map_filter_dict(get_ipa, pronunciation)
        ipa_lenient, _ = map_filter_dict(get_ipa_lenient, pronunciation)
        diff = diff_dict(ipa_lenient, ipa)
        self.assertGreater(len(ipa_lenient), 32000)
        self.assertGreater(len(diff), 200)

        ## future possibility: match [brackets] for phonetic transcriptions
        ## as opposed to just the phonemic transcriptions within /slashes/
        # with self.subTest(word='accend'):
        #     pron = ("===Pronunciation===\n"
        #             "* {{IPA|[\u00e6k\u02c8s\u025bnd]|lang=en}}\n\n")
        #     ipa = "[[\u00e6k\u02c8s\u025bnd]]"
        #     self.assertEqual(get_ipa(pron), ipa)


if __name__ == '__main__':
    unittest.main()
