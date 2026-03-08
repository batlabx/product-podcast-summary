import unittest

import summarize


class TestSummarize(unittest.TestCase):
    def test_clean_sentence_removes_speaker_and_timestamp(self):
        raw = "Lenny Rachitsky (00:12:34): This is a useful product lesson for teams."
        cleaned = summarize.clean_sentence(raw)
        self.assertEqual(cleaned, "This is a useful product lesson for teams.")

    def test_is_noise_filters_ads(self):
        self.assertTrue(summarize.is_noise("This episode is brought to you by ExampleCorp."))

    def test_summarize_returns_points(self):
        text = (
            "Product teams need clear priorities and fast feedback loops. "
            "Lenny Rachitsky (00:11:22): This episode is brought to you by ACME. "
            "Great PMs communicate trade-offs clearly and align stakeholders early. "
            "The best leaders simplify complexity and repeat strategy often for clarity."
        )
        bullets = summarize.summarize_text(text, n=3)
        self.assertGreaterEqual(len(bullets), 2)
        self.assertTrue(all("brought to you" not in b.lower() for b in bullets))


if __name__ == "__main__":
    unittest.main()
