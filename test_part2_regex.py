# 1. Install dev packages via `pipenv sync --dev`
# 2. `pipenv run pytest`

from part2_regex import parse_dimensions


def test_parse_dimensions():
    assert parse_dimensions('19×52cm') == (19, 52, None)
    assert parse_dimensions('50 x 66,4 cm') == (50, 66.4, None)
    assert parse_dimensions('168.9 x 274.3 x 3.8 cm (66 1/2 x 108 x 1 1/2 in.) 	') == (168.9, 274.3, 3.8)
    assert parse_dimensions('Sheet: 16 1/4 × 12 1/4 in. (41.3 × 31.1 cm) Image: 14 × 9 7/8 in. (35.6 × 25.1 cm)') == (35.6, 25.1, None)
    assert parse_dimensions('5 by 5in') == (12.7, 12.7, None)
    assert parse_dimensions('12 x 20 cm') == (12, 20, None)
    assert parse_dimensions('84cms x 59cms') == (84, 59, None)
    assert parse_dimensions('60cm  diam') == (60, 60, None)
    assert parse_dimensions('40.7 x 50.8') == (40.7, 50.8, None)
