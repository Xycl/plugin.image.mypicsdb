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
from resources.lib.Meta import Reader


class MetaReaderTest(unittest.TestCase):

    def test_get_meta(self):

        expected_meta_ = {
            'Image RatingPercent': '0',
            'Image Rating': '0',
            'Image Model': 'DMC-G3',
            'Image XResolution': '180',
            'Image Make': 'Panasonic',
            'Image DateTime': '2014-04-16 11:55:16',
            'Image YResolution': '180',
            'Image ResolutionUnit': 'Pixels/Inch',
            'supplemental category': '',
            'contact': '',
            'keywords': u'Show:Friends',
            'EXIF FileSource': 'Digital Camera',
            'EXIF DateTimeDigitized': '2014-04-16 11:55:16',
            'EXIF DateTimeOriginal': '2014-04-16 11:55:16',
            'EXIF Flash': 'Flash did not fire, compulsory flash mode',
            'EXIF ExifImageLength': '4592',
            'EXIF ExifVersion': '0230',
            'EXIF ExifImageWidth': '3448'
        }

        self.assertMetas(expected_meta_, Reader('./testData/badFile.jpg').get_metas())

    def assertMetas(self, expected_metas_, actual_metas_):

        for key_to_test in expected_metas_:
            self.assertTrue(key_to_test in actual_metas_, 'Testing key: "%s"' % key_to_test)

            if key_to_test in actual_metas_:
                self.assertEqual(expected_metas_[key_to_test], actual_metas_[key_to_test], 'Testing key: %s' % key_to_test)

        self.assertEqual(len(expected_metas_), len(actual_metas_))
