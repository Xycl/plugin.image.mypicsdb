# -*- coding: utf8 -*-
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

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