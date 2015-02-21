import wikiparser as wp
import unittest
import os
import json

class TestFunctions(unittest.TestCase):

    @unittest.skip('will not be using until refactor or next data dump')
    def test_xml_to_wikitext(self):
        test_xml_file = 'test/small.xml'
        test_out = 'test/test.tmp'
        words_found = wp.parse_xml_to_json(test_xml_file, test_out)
        os.remove(test_out)
        words_expected = 19
        self.assertEqual(words_found, words_expected)

    def test_normalize_filename_empty_input(self):
        self.assertEqual('', wp.normalize_filename(''))

class TestWikitext(unittest.TestCase):

    # NOTE: this test fixture should slowly be phased out.
    # when possible, rewrite into minimal test cases that capture behavior
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

    def test_extract_ipa_examples(self):
        for word, text in self.examples.items():
            if 'pron' in text and 'ipa' in text:
                comment = text['comment'] if 'comment' in text else None
                with self.subTest(word=word, comment=comment):
                    expected = text['ipa']
                    pron = wp.Wikitext(text['pron']).extract_pronunciation()
                    result = list(ipa_object['ipa'] for ipa_object in pron['ipa'])
                    self.assertEqual(expected, result)

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

    def test_extract_ipa_skips_ipachar(self):
        text = (
            '** {{a|UK}} {{enPR|yo\u035eo}}, {{audio-IPA|En-uk-you.ogg|/ju\u02d0/|lang=en}}\n'
            '** {{a|US}} {{enPR|yo\u035eo}}, {{audio-IPA|en-us-you.ogg|/ju/|lang=en}}\n'
            '** {{a|US}} {{enPR|y\u0259}}, {{audio-IPA|en-us-you unstressed.ogg|/j\u0259/|lang=en}}\n'
            'When a word ending in {{IPAchar|/t/}}, {{IPAchar|/d/}}, {{IPAchar|/s/}}, '
            'or {{IPAchar|/z/}} is followed by {{term|you|lang=en}}, '
            'these may coalesce with the {{IPAchar|/j/}}, resulting in {{IPAchar|/t\u0283/}}, '
            '{{IPAchar|/d\u0292/}}, {{IPAchar|/\u0283/}} and {{IPAchar|/\u0292/}}, respectively. '
        )
        expected_ipa = [
            {'ipa': '/ju\u02d0/', 'accent': 'GB'},
            {'ipa': '/ju/', 'accent': 'US'},
            {'ipa': '/j\u0259/', 'accent': 'US'}
        ]
        pron = wp.Wikitext(text).extract_pronunciation()
        result_ipa = pron['ipa']
        self.assertEqual(expected_ipa, result_ipa)

    def test_extract_ipa_skips_brackets(self):
        text = '* {{a|UK}} {{IPA|[\u02c8d\u026ad\u0259\u026b]|lang=en}}\n'
        extracted_pron = wp.Wikitext(text).extract_pronunciation()
        self.assertNotIn('ipa', extracted_pron)

    def test_extract_ipa_skips_links(self):
        text = '[http://www.wordreference.com/definition/pecan pecan]'
        extracted_pron = wp.Wikitext(text).extract_pronunciation()
        self.assertNotIn('ipa', extracted_pron)

    # NOTE: long test
    def test_extract_ipa_meets_threshold(self):
        pronunciation = wp.json_load('test/pron.json')
        self.assertGreater(len(pronunciation), 45000)

        # dictionaries from words to lists of ipa
        ipa = {}
        ipa_lenient = {}
        for word, pron_section in pronunciation.items():
            pron_info = wp.Wikitext(pron_section).extract_pronunciation()
            if 'ipa' in pron_info:
                ipa[word] = pron_info['ipa']

            ipa_lenient_results = wp.Wikitext(pron_section).extract_ipa_lenient()
            if ipa_lenient_results:
                ipa_lenient[word] = ipa_lenient_results

        ipa_diff = {k: pronunciation[k] for k in ipa_lenient.keys()
                    if k not in ipa or len(ipa_lenient[k]) > len(ipa[k])}
        self.assertGreater(len(ipa_lenient), 32000)
        self.assertGreater(len(ipa), 32000)
        self.assertGreater(len(ipa_diff), 500)

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
