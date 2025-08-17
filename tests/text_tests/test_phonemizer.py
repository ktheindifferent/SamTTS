import unittest

from TTS.tts.utils.text.phonemizers import ESpeak, Gruut, JA_JP_Phonemizer, ZH_CN_Phonemizer

EXAMPLE_TEXTs = [
    "Recent research at Harvard has shown meditating",
    "for as little as 8 weeks can actually increase, the grey matter",
    "in the parts of the brain responsible",
    "for emotional regulation and learning!",
]


EXPECTED_ESPEAK_PHONEMES = [
    "ɹ|ˈiː|s|ə|n|t ɹ|ɪ|s|ˈɜː|tʃ æ|t h|ˈɑːɹ|v|ɚ|d h|ɐ|z ʃ|ˈoʊ|n m|ˈɛ|d|ɪ|t|ˌeɪ|ɾ|ɪ|ŋ",
    "f|ɔː|ɹ æ|z l|ˈɪ|ɾ|əl æ|z ˈeɪ|t w|ˈiː|k|s k|æ|n ˈæ|k|tʃ|uː|əl|i| ˈɪ|n|k|ɹ|iː|s, ð|ə ɡ|ɹ|ˈeɪ m|ˈæ|ɾ|ɚ",
    "ɪ|n|ð|ə p|ˈɑːɹ|t|s ʌ|v|ð|ə b|ɹ|ˈeɪ|n ɹ|ɪ|s|p|ˈɑː|n|s|ə|b|əl",
    "f|ɔː|ɹ ɪ|m|ˈoʊ|ʃ|ə|n|əl ɹ|ˌɛ|ɡ|j|uː|l|ˈeɪ|ʃ|ə|n|| æ|n|d l|ˈɜː|n|ɪ|ŋ!",
]


EXPECTED_ESPEAKNG_PHONEMES = [
    "ɹ|ˈiː|s|ə|n|t ɹ|ᵻ|s|ˈɜː|tʃ æ|t h|ˈɑːɹ|v|ɚ|d h|ɐ|z ʃ|ˈoʊ|n m|ˈɛ|d|ᵻ|t|ˌeɪ|ɾ|ɪ|ŋ",
    "f|ɔː|ɹ æ|z l|ˈɪ|ɾ|əl æ|z ˈeɪ|t w|ˈiː|k|s k|æ|n ˈæ|k|tʃ|uː|əl|i| ˈɪ|ŋ|k|ɹ|iː|s, ð|ə ɡ|ɹ|ˈeɪ m|ˈæ|ɾ|ɚ",
    "ɪ|n|ð|ə p|ˈɑːɹ|t|s ʌ|v|ð|ə b|ɹ|ˈeɪ|n ɹ|ᵻ|s|p|ˈɑː|n|s|ᵻ|b|əl",
    "f|ɔː|ɹ ɪ|m|ˈoʊ|ʃ|ə|n|əl ɹ|ˌɛ|ɡ|j|ʊ|l|ˈeɪ|ʃ|ə|n|| æ|n|d l|ˈɜː|n|ɪ|ŋ!",
]


class TestEspeakPhonemizer(unittest.TestCase):
    def setUp(self):
        self.phonemizer = ESpeak(language="en-us", backend="espeak")

        for text, ph in zip(EXAMPLE_TEXTs, EXPECTED_ESPEAK_PHONEMES):
            phonemes = self.phonemizer.phonemize(text)
            self.assertEqual(phonemes, ph)

        # multiple punctuations
        text = "Be a voice, not an! echo?"
        gt = "biː ɐ vˈɔɪs, nˈɑːt ɐn! ˈɛkoʊ?"
        output = self.phonemizer.phonemize(text, separator="|")
        output = output.replace("|", "")
        self.assertEqual(output, gt)

        # not ending with punctuation
        text = "Be a voice, not an! echo"
        gt = "biː ɐ vˈɔɪs, nˈɑːt ɐn! ˈɛkoʊ"
        output = self.phonemizer.phonemize(text, separator="")
        self.assertEqual(output, gt)

        # extra space after the sentence
        text = "Be a voice, not an! echo.  "
        gt = "biː ɐ vˈɔɪs, nˈɑːt ɐn! ˈɛkoʊ."
        output = self.phonemizer.phonemize(text, separator="")
        self.assertEqual(output, gt)

    def test_name(self):
        self.assertEqual(self.phonemizer.name(), "espeak")

    def test_get_supported_languages(self):
        self.assertIsInstance(self.phonemizer.supported_languages(), dict)

    def test_get_version(self):
        self.assertIsInstance(self.phonemizer.version(), str)

    def test_is_available(self):
        self.assertTrue(self.phonemizer.is_available())


class TestEspeakNgPhonemizer(unittest.TestCase):
    def setUp(self):
        self.phonemizer = ESpeak(language="en-us", backend="espeak-ng")

        for text, ph in zip(EXAMPLE_TEXTs, EXPECTED_ESPEAKNG_PHONEMES):
            phonemes = self.phonemizer.phonemize(text)
            self.assertEqual(phonemes, ph)

        # multiple punctuations
        text = "Be a voice, not an! echo?"
        gt = "biː ɐ vˈɔɪs, nˈɑːt æn! ˈɛkoʊ?"
        output = self.phonemizer.phonemize(text, separator="|")
        output = output.replace("|", "")
        self.assertEqual(output, gt)

        # not ending with punctuation
        text = "Be a voice, not an! echo"
        gt = "biː ɐ vˈɔɪs, nˈɑːt æn! ˈɛkoʊ"
        output = self.phonemizer.phonemize(text, separator="")
        self.assertEqual(output, gt)

        # extra space after the sentence
        text = "Be a voice, not an! echo.  "
        gt = "biː ɐ vˈɔɪs, nˈɑːt æn! ˈɛkoʊ."
        output = self.phonemizer.phonemize(text, separator="")
        self.assertEqual(output, gt)

    def test_name(self):
        self.assertEqual(self.phonemizer.name(), "espeak")

    def test_get_supported_languages(self):
        self.assertIsInstance(self.phonemizer.supported_languages(), dict)

    def test_get_version(self):
        self.assertIsInstance(self.phonemizer.version(), str)

    def test_is_available(self):
        self.assertTrue(self.phonemizer.is_available())


class TestGruutPhonemizer(unittest.TestCase):
    def setUp(self):
        self.phonemizer = Gruut(language="en-us", use_espeak_phonemes=True, keep_stress=False)
        self.EXPECTED_PHONEMES = [
            "ɹ|i|ː|s|ə|n|t| ɹ|ᵻ|s|ɜ|ː|t|ʃ| æ|ɾ| h|ɑ|ː|ɹ|v|ɚ|d| h|ɐ|z| ʃ|o|ʊ|n| m|ɛ|d|ᵻ|t|e|ɪ|ɾ|ɪ|ŋ",
            "f|ɔ|ː|ɹ| æ|z| l|ɪ|ɾ|ə|l| æ|z| e|ɪ|t| w|i|ː|k|s| k|æ|ŋ| æ|k|t|ʃ|u|ː|ə|l|i| ɪ|ŋ|k|ɹ|i|ː|s, ð|ə| ɡ|ɹ|e|ɪ| m|æ|ɾ|ɚ",
            "ɪ|n| ð|ə| p|ɑ|ː|ɹ|t|s| ʌ|v| ð|ə| b|ɹ|e|ɪ|n| ɹ|ᵻ|s|p|ɑ|ː|n|s|ᵻ|b|ə|l",
            "f|ɔ|ː|ɹ| ɪ|m|o|ʊ|ʃ|ə|n|ə|l| ɹ|ɛ|ɡ|j|ʊ|l|e|ɪ|ʃ|ə|n| æ|n|d| l|ɜ|ː|n|ɪ|ŋ!",
        ]

    def test_phonemize(self):
        for text, ph in zip(EXAMPLE_TEXTs, self.EXPECTED_PHONEMES):
            phonemes = self.phonemizer.phonemize(text, separator="|")
            self.assertEqual(phonemes, ph)

        # multiple punctuations
        text = "Be a voice, not an! echo?"
        gt = "biː ɐ vɔɪs, nɑːt ɐn! ɛkoʊ?"
        output = self.phonemizer.phonemize(text, separator="|")
        output = output.replace("|", "")
        self.assertEqual(output, gt)

        # not ending with punctuation
        text = "Be a voice, not an! echo"
        gt = "biː ɐ vɔɪs, nɑːt ɐn! ɛkoʊ"
        output = self.phonemizer.phonemize(text, separator="")
        self.assertEqual(output, gt)

        # extra space after the sentence
        text = "Be a voice, not an! echo.  "
        gt = "biː ɐ vɔɪs, nɑːt ɐn! ɛkoʊ."
        output = self.phonemizer.phonemize(text, separator="")
        self.assertEqual(output, gt)

    def test_name(self):
        self.assertEqual(self.phonemizer.name(), "gruut")

    def test_get_supported_languages(self):
        self.assertIsInstance(self.phonemizer.supported_languages(), list)

    def test_get_version(self):
        self.assertIsInstance(self.phonemizer.version(), str)

    def test_is_available(self):
        self.assertTrue(self.phonemizer.is_available())


class TestJA_JPPhonemizer(unittest.TestCase):
    def setUp(self):
        self.phonemizer = JA_JP_Phonemizer()
        self._TEST_CASES = """
            どちらに行きますか？/dochiraniikimasuka?
            今日は温泉に、行きます。/kyo:waoNseNni,ikimasu.
            「A」から「Z」までです。/e:karazeqtomadedesu.
            そうですね！/so:desune!
            クジラは哺乳類です。/kujirawahonyu:ruidesu.
            ヴィディオを見ます。/bidioomimasu.
            今日は８月22日です/kyo:wahachigatsuniju:ninichidesu
            xyzとαβγ/eqkusuwaizeqtotoarufabe:tagaNma
            値段は$12.34です/nedaNwaju:niteNsaNyoNdorudesu
            """

    def test_phonemize(self):
        for line in self._TEST_CASES.strip().split("\n"):
            text, phone = line.split("/")
            self.assertEqual(self.phonemizer.phonemize(text, separator=""), phone)

    def test_name(self):
        self.assertEqual(self.phonemizer.name(), "ja_jp_phonemizer")

    def test_get_supported_languages(self):
        self.assertIsInstance(self.phonemizer.supported_languages(), dict)

    def test_get_version(self):
        self.assertIsInstance(self.phonemizer.version(), str)

    def test_is_available(self):
        self.assertTrue(self.phonemizer.is_available())


class TestZH_CN_Phonemizer(unittest.TestCase):
    def setUp(self):
        self.phonemizer = ZH_CN_Phonemizer()
        self._TEST_CASES = ""

    def test_phonemize(self):
        """Test Chinese phonemization with various inputs."""
        # Test basic Chinese text phonemization
        test_cases = [
            # (input, expected_contains)
            ("你好", ["n", "i", "3", "h", "ɑ", "o", "3"]),  # "ni hao" in phonemes
            ("中国", ["d", "ʒ", "o", "ŋ", "1", "g", "u", "o", "2"]),  # "zhong guo"
            ("我爱你", ["w", "o", "3", "a", "i", "4", "n", "i", "3"]),  # "wo ai ni"
            ("测试", ["t", "s", "ø", "4", "ʂ", "ʏ", "4"]),  # "ce shi"
            ("一二三", ["i", "1", "ø", "r", "4", "s", "a", "n", "1"]),  # "yi er san"
        ]
        
        for text, expected_phonemes in test_cases:
            result = self.phonemizer.phonemize(text, separator="|")
            # Check that key phonemes are present
            for phoneme in expected_phonemes:
                self.assertIn(phoneme, result, f"Expected phoneme '{phoneme}' not found in result for '{text}'")
        
        # Test with punctuation (should be preserved if keep_puncs=True)
        self.phonemizer.keep_puncs = True
        text_with_punct = "你好，世界！"
        result_with_punct = self.phonemizer.phonemize(text_with_punct, separator="|")
        self.assertIn("，", result_with_punct)
        self.assertIn("！", result_with_punct)
        
        # Test with punctuation removed (keep_puncs=False)
        self.phonemizer.keep_puncs = False
        result_no_punct = self.phonemizer.phonemize(text_with_punct, separator="|")
        self.assertNotIn("，", result_no_punct)
        self.assertNotIn("！", result_no_punct)
        
        # Test empty string
        empty_result = self.phonemizer.phonemize("", separator="|")
        self.assertEqual(empty_result, "")
        
        # Test with mixed Chinese and punctuation
        mixed_text = "这是，样本中文。"
        mixed_result = self.phonemizer.phonemize(mixed_text, separator="|")
        # Should contain phonemes for all Chinese characters
        self.assertIn("d", mixed_result)  # from "这"
        self.assertIn("ʂ", mixed_result)  # from "是"
        
        # Test with numbers (Chinese numbers should be phonemized)
        number_text = "一个人"
        number_result = self.phonemizer.phonemize(number_text, separator="|")
        self.assertIn("i", number_result)  # from "一"
        self.assertIn("g", number_result)  # from "个"
        self.assertIn("r", number_result)  # from "人"
        
        # Test separator functionality
        test_sep = " "
        sep_result = self.phonemizer.phonemize("你好", separator=test_sep)
        self.assertNotIn("|", sep_result)
        self.assertIn(" ", sep_result)

    def test_name(self):
        self.assertEqual(self.phonemizer.name(), "zh_cn_phonemizer")

    def test_get_supported_languages(self):
        self.assertIsInstance(self.phonemizer.supported_languages(), dict)

    def test_get_version(self):
        self.assertIsInstance(self.phonemizer.version(), str)

    def test_is_available(self):
        self.assertTrue(self.phonemizer.is_available())
