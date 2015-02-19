import wikiparser as wp
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
        cls.examples = wp.json_load('test/wikitext_examples.json')

    @unittest.skip('will not be using until refactor or next data dump')
    def test_xml_to_wikitext(self):
        test_xml_file = 'test/small.xml'
        test_out = 'test/test.tmp'
        words_found = wp.parse_xml_to_json(test_xml_file, test_out)
        os.remove(test_out)
        words_expected = 19
        self.assertEqual(words_found, words_expected)

    def _test_examples_parse_step(self, from_label, to_label):
        """helper method to test specific parse steps"""
        step_names = ['text', 'lang', 'pron', 'ipa']
        self.assertIn(from_label, step_names)
        self.assertIn(to_label, step_names)
        map_functions = {'lang': wp.get_english,
                         'pron': wp.get_pronunciation,
                         'ipa': wp.get_ipa}
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

    @unittest.skip('refactoring')
    def test_extract_language_section(self):
        self._test_examples_parse_step('text', 'lang')

    @unittest.skip('refactoring')
    def test_extract_pronunciation_section(self):
        self._test_examples_parse_step('lang', 'pron')

    @unittest.skip('refactoring')
    def test_extract_ipa(self):
        self._test_examples_parse_step('pron', 'ipa')
        # word: impasse
        # word: eschew
        # word: garage
        # word: hoping
        # count number of ipa to find bugs

        pronunciation = wp.json_load('test/pron.json')
        self.assertGreater(len(pronunciation), 45000)

        ipa, no_ipa = wp.map_filter_dict(get_ipa, pronunciation)
        ipa_lenient, _ = wp.map_filter_dict(get_ipa_lenient, pronunciation)
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

    @unittest.skip('refactoring')
    def test_get_templates(self):
        wikitext = ("* {{a|US}} {{enPR|mī-ăz'mə|mē- ăz'mə}}, "
                    "{{IPA|/maɪˈæzmə/|/miˈæzmə/|lang=en}}")
        templates = wp.get_templates(wikitext)
        expected = [['a', 'US'],
                    ['enPR', "mī-ăz'mə", "mē- ăz'mə"],
                    ['IPA', '/maɪˈæzmə/', '/miˈæzmə/', 'lang=en']]
        self.assertEqual(expected, templates)

class TestWikitext(unittest.TestCase):

    def test_filter_sections(self):
        # don't naively count '=' to determine heading level
        text = (
            '==Section==\n'
            '{{template|p1=1|p2=2|p3=3|p4=4}}\n'
            'then it ends\n'
            '==Next Section==\n'
        )
        filtered = wp.Wikitext(text).filter_sections('section')
        expected = (
            '==Section==\n'
            '{{template|p1=1|p2=2|p3=3|p4=4}}\n'
            'then it ends\n'
        )
        self.assertEqual(expected, filtered)


if __name__ == '__main__':
    # temp setup to help testing
    if 0:
        folder = 'out/'
        pron = wp.json_load(folder + 'pron.json')
        ipa = wp.json_load(folder + 'ipa.json')
        ipa_lenient = wp.json_load(folder + 'ipa_lenient.json')
        hit, miss = wp.map_filter_dict(get_ipa_test, pron)
        diff_lenient = {k: pron[k] for k in ipa_lenient.keys()
                        if k not in hit or len(ipa_lenient[k]) > len(hit[k])}
        diff_prev = {k: pron[k] for k in ipa.keys()
                     if k not in hit or len(ipa[k]) > len(hit[k])}
        wp.json_dump(hit, 'test/hit.tmp.json')
        #wp.json_dump(miss, 'test/miss.tmp.json')
        wp.json_dump(diff_lenient, 'test/diff_lenient.tmp.json')
        wp.json_dump(diff_prev, 'test/diff_prev.tmp.json')
    else:
        unittest.main()
