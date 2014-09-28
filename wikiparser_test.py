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

    @unittest.skip('will not be using until refactor or next data dump')
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
        for example in self.examples:
            with self.subTest(word=example['word']):
                ipa = get_ipa(example['pron'])
                self.assertEqual(sorted(ipa), sorted(example['ipa']))
        with self.subTest(word='oxypnictide'):
            pron = "===Pronunciation===\nOXEE-nick-tyde <ref> Space Daily; [http://www.spacedaily.com/reports/Quantum_criticality_observed_in_new_class_of_materials_999.html \"Quantum criticality observed in new class of materials\"]; 5 June 2014 </ref>\n\n"
            ipa = get_ipa(pron)
            self.assertEqual(sorted(ipa), [])
        # catch the 4 correct IPA but neither the link, nor embedded note IPA
        with self.subTest(word='adversary'):
            pron = "===Pronunciation===\n* {{a|UK}} {{IPA|/\u02c8\u00e6d.v\u0259.s(\u0259)\u0279i/|lang=en}}<ref>[http://dictionary.cambridge.org/define.asp?key=1216&amp;dict=CALD Cambridge Advanced Learner's Dictionary]</ref>\n* {{a|UK}} {{IPA|/\u02c8\u00e6d.v\u0259.s\u025b\u0279i/|lang=en}}<ref>According to UK audio file in Longman Exams Dictionary, even though IPA given in dictionary is /\u02c8\u00e6d.v\u0259.s(\u0259)\u0279i\u02d0/</ref>\n* {{a|UK}} {{IPA|/\u00e6d\u02c8v\u025c\u02d0.s\u0259.\u0279i/|lang=en}}\n* {{a|US}} {{IPA|/\u02c8\u00e6d.v\u0259\u0279.s\u025b\u0279i/|lang=en}}\n* {{audio|en-us-adversary.ogg|Audio (US)|lang=en}}\n\n"
            ipa_list = get_ipa(pron)
            expected = ["/\u02c8\u00e6d.v\u0259.s(\u0259)\u0279i/",
                        "/\u02c8\u00e6d.v\u0259.s\u025b\u0279i/",
                        "/\u00e6d\u02c8v\u025c\u02d0.s\u0259.\u0279i/",
                        "/\u02c8\u00e6d.v\u0259\u0279.s\u025b\u0279i/"]
            self.assertEqual(ipa_list, expected)
        # extra section between IPA label and actual IPA
        with self.subTest(word='mishap'):
            pron = "===Pronunciation===\n* {{IPA|lang=en|/\u02c8m\u026as.h\u00e6p/}}\n\n"
            ipa_list = get_ipa(pron)
            expected = ["/\u02c8m\u026as.h\u00e6p/"]
            self.assertEqual(ipa_list, expected)
        # word: hoping
        # word: pecan
        # word: diddle

        # using lenient matching for everything within /slashes/: r'/[^/]+/'
        # from full english wordlist: 32028 potential ipa, 12806 without
        with open('words_with_ipa1.json', 'r', encoding='utf-8') as f:
            ipa1_list = json.load(f)
        ipa1_dict = {w['word']: w['ipa'] for w in ipa1_list}
        with open('words_with_pronunciation.json', 'r', encoding='utf-8') as f:
            pron_list = json.load(f)
        pron_dict = {w['word']: w['pron'] for w in pron_list}

        with_ipa, without_ipa = parse_to_dicts(pron_list, get_ipa)
        missing_from_ipa1 = []
        for word in with_ipa:
            if word not in ipa1_dict:
                missing_from_ipa1.append(word)
        if missing_from_ipa1:
            print('missing from ipa1:', len(missing_from_ipa1))
            assert False
        diff = []
        for word in ipa1_dict:
            if word not in with_ipa:
                diff.append({"word": word, "pron": pron_dict[word]})
#        # output diff to tmp file for examination
#        if diff:
#            out = 'test/diff.tmp'
#            with open(out, 'w', encoding='utf-8') as f:
#                json.dump(diff, f, indent=2)
#            print('length of diff:', len(diff))
#        # output new ipa list to tmp file for examination
#        new_ipa_list = [{word: ipa} for word, ipa in with_ipa.items()]
#        out = 'test/new_ipa.tmp'
#        with open(out, 'w', encoding='utf-8') as f:
#            json.dump(new_ipa_list, f, indent=2)

#        import code; code.interact(local=dict(globals(), **locals()))


        ## future possibility: match [brackets] for phonetic transcriptions
        ## as opposed to just the phonemic transcriptions within /slashes/
        # with self.subTest(word='accend'):
        #     pron = ("===Pronunciation===\n"
        #             "* {{IPA|[\u00e6k\u02c8s\u025bnd]|lang=en}}\n\n")
        #     ipa = "[[\u00e6k\u02c8s\u025bnd]]"
        #     self.assertEqual(get_ipa(pron), ipa)


if __name__ == '__main__':
    unittest.main()
