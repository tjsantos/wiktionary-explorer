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
            with self.subTest(word=word, comment=comment,
                              step=(from_label, to_label)):
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

        pronunciation = json_load('test/pron.json')
        self.assertGreater(len(pronunciation), 45000)

        ipa, no_ipa = map_filter_dict(get_ipa, pronunciation)
        ipa_lenient, _ = map_filter_dict(get_ipa_lenient, pronunciation)
        ipa_diff = {k: pronunciation[k] for k in ipa_lenient.keys()
                    if k not in ipa or len(ipa_lenient[k]) > len(ipa[k])}
        self.assertGreater(len(ipa_lenient), 32000)
        self.assertGreater(len(ipa), 32000)
        self.assertGreater(len(ipa_diff), 500)

        ## future possibility: match [brackets] for phonetic transcriptions
        ## as opposed to just the phonemic transcriptions within /slashes/
        # with self.subTest(word='accend'):
        #     pron = ("===Pronunciation===\n"
        #             "* {{IPA|[\u00e6k\u02c8s\u025bnd]|lang=en}}\n\n")
        #     ipa = "[[\u00e6k\u02c8s\u025bnd]]"
        #     self.assertEqual(get_ipa(pron), ipa)


if __name__ == '__main__':
    # temp setup to help testing
    if 0:
        pron = json_load('pron.json')
        ipa = json_load('ipa.json')
        ipa_lenient = json_load('ipa_lenient.json')
        hit, miss = map_filter_dict(get_ipa, pron)
        diff = {k: pron[k] for k in ipa_lenient.keys()
                    if k not in hit or len(ipa_lenient[k]) > len(hit[k])}
        json_dump(hit, 'test/hit.tmp.json')
        #json_dump(miss, 'test/miss.tmp.json')
        json_dump(diff, 'test/diff.tmp.json')
    else:
        unittest.main()
