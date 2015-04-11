__author__ = 'MaWoe'

import unittest
from resources.lib.ImageRating import Reader


class ImageRatingReaderTest(unittest.TestCase):

    def test_get_rating(self):
        self.assertEqual(Reader({'Image Rating': 0}).get_rating(), '0')
        self.assertEqual(Reader({'Image Rating': '1'}).get_rating(), '1')
        self.assertEqual(Reader({
            'Image Rating': '10',
            'xmp:Rating': '1'
        }).get_rating(), '10')

    def test_override_by_xmp_rating(self):
        self.assertEqual(Reader({
            'Image Rating': None,
            'xmp:Rating': '1'
        }).get_rating(), '1')

    def test_override_by_xap_rating(self):
        self.assertEqual(Reader({
            'Image Rating': None,
            'xap:Rating': '1'
        }).get_rating(), '1')

    def test_percentage_conversion(self):

        percentage_to_rating_map = {
            00: '0',
            01: '1',
            24: '1',
            25: '2',
            48: '2',
            50: '3',
            75: '4',
            94: '4',
            95: '5'
        }

        for percentage in percentage_to_rating_map:
            expected_rating = percentage_to_rating_map[percentage]

            self.assertEqual(Reader({
                'Image Rating': None,
                'Image RatingPercent': str(percentage)
            }).get_rating(), expected_rating)

if __name__ == '__main__':
    unittest.main()