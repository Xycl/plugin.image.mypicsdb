__author__ = 'MaWoe'


class Reader:
    def __init__(self, picentry):
        self.picentry = picentry

    def get_rating(self):
        picentry = self.picentry

        image_rating = picentry['Image Rating']
        if image_rating is None or image_rating == '' or image_rating < '1':
            if 'xmp:Rating' in picentry and (picentry['xmp:Rating'] is not None or picentry['xmp:Rating'] != ''):
                image_rating = picentry['xmp:Rating']
            elif 'xap:Rating' in picentry and (picentry['xap:Rating'] is not None or picentry['xap:Rating'] != ''):
                image_rating = picentry['xap:Rating']
            elif 'Image RatingPercent' in picentry and (picentry['Image RatingPercent'] is not None or picentry['Image RatingPercent'] != ''):
                a = int(picentry['Image RatingPercent'])
                if a >= 95:
                    new_rating = 5
                elif a >= 75:
                    new_rating = 4
                elif a >= 50:
                    new_rating = 3
                elif a >= 25:
                    new_rating = 2
                elif a >= 1:
                    new_rating = 1
                else:
                    new_rating = 0
                image_rating = new_rating

        if image_rating is None or (type(image_rating) is str and len(image_rating) == 0):
            image_rating = "0"

        return str(image_rating)
