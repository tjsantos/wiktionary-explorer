import wikiparser as wp
import unittest
import os
import json

class TestParser(unittest.TestCase):


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
    def test_extract_ipa(self):
        self._test_examples_parse_step('pron', 'ipa')

        pronunciation = wp.json_load('test/pron.json')
        self.assertGreater(len(pronunciation), 45000)

        ipa, no_ipa = wp.map_filter_dict(get_ipa, pronunciation)
        ipa_lenient, _ = wp.map_filter_dict(get_ipa_lenient, pronunciation)
        ipa_diff = {k: pronunciation[k] for k in ipa_lenient.keys()
                    if k not in ipa or len(ipa_lenient[k]) > len(ipa[k])}
        self.assertGreater(len(ipa_lenient), 32000)
        self.assertGreater(len(ipa), 32000)
        self.assertGreater(len(ipa_diff), 500)

class TestWikitext(unittest.TestCase):

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

    def test_filter_section_does_not_change(self):
        text = (
            '==English==\n\n'
            '===Noun===\n'
            '{{en-noun|head=[[mu]]-[[meson]]}}\n\n'
            '# a [[subatomic particle]], now [[contract]]ed to [[muon]].\n\n'
            '[[Category:en:Subatomic particles]]"'
        )
        expected = text
        filtered = wp.Wikitext(text).filter_sections('english')
        self.assertEqual(expected, filtered)

    def test_filter_two_sections(self):
        text = (
            '==English==\n\n'
            '===Etymology 1===\n'
            "An [[aphetic]] form of ''[[banana]]''.\n\n"
            '====Pronunciation====\n'
            '* {{enPR|n\u00e4\u02b9n\u0259}}, {{IPA|/\u02c8n\u0251\u02d0n\u0259/|lang=en}}\n'
            '===Etymology 2===\n'
            "Variant spelling of ''[[nanna]]''.\n\n"
            '====Pronunciation====\n'
            '* {{enPR|n\u0103n\u02b9\u0259}}, {{IPA|/\u02c8n\u00e6n\u0259/|lang=en}}\n'
        )
        expected = (
            '====Pronunciation====\n'
            '* {{enPR|n\u00e4\u02b9n\u0259}}, {{IPA|/\u02c8n\u0251\u02d0n\u0259/|lang=en}}\n'
            '====Pronunciation====\n'
            '* {{enPR|n\u0103n\u02b9\u0259}}, {{IPA|/\u02c8n\u00e6n\u0259/|lang=en}}\n'
        )
        filtered = wp.Wikitext(text).filter_sections('pronunciation')
        self.assertEqual(expected, filtered)

    def test_filter_language_examples(self):
        for word, text in self.examples.items():
            if 'text' in text and 'lang' in text:
                comment = text['comment'] if 'comment' in text else None
                with self.subTest(word=word, comment=comment):
                    expected = text['lang']
                    result = wp.Wikitext(text['text']).filter_sections('english')
                    self.assertEqual(expected, result)

    def test_filter_pronunciation_examples(self):
        for word, text in self.examples.items():
            if 'pron' in text and 'lang' in text:
                comment = text['comment'] if 'comment' in text else None
                with self.subTest(word=word, comment=comment):
                    expected = text['pron']
                    result = wp.Wikitext(text['lang']).filter_sections('pronunciation')
                    self.assertEqual(expected, result)

    def test_tokenize_templates(self):
        text = ("* {{a|US}} {{enPR|mī-ăz'mə|mē- ăz'mə}}, "
                "{{IPA|/maɪˈæzmə/|/miˈæzmə/|lang=en}}")
        tokens = wp.Wikitext(text).tokenize_templates()
        expected = [
            '* ',
            ['a', 'US'],
            ' ',
            ['enPR', "mī-ăz'mə", "mē- ăz'mə"],
            ', ',
            ['IPA', '/maɪˈæzmə/', '/miˈæzmə/', 'lang=en']
        ]
        self.assertEqual(expected, tokens)

class TestWikitemplate(unittest.TestCase):

    def test_parse(self):
        '''Don't parse inner templates'''
        text = '{{a|1|2|{{b|3|4}}}}'
        template = wp.Wikitemplate.parse(text)
        expected = ['a', '1', '2', '{{b|3|4}}']
        self.assertEqual(expected, template)

if __name__ == '__main__':
    unittest.main()
