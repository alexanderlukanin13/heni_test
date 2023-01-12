import re
from collections import namedtuple
from math import isnan

import pandas as pd


def _build_dimensions_regexes():
    # Temporary function to build list of regexes for matching dimensions.
    # It's a good idea to use clear building blocks, instead of long, repetitive regexes,
    # which are painful to maintain.
    num = r'(?:\d+(?:[.,]\d+|\s+\d+/\d+)?)'
    height = fr'(?P<height>{num})'
    width = fr'(?P<width>{num})'
    depth = fr'(?P<depth>{num})'
    height2 = fr'(?P<height2>{num})'
    width2 = fr'(?P<width2>{num})'
    depth2 = fr'(?P<depth2>{num})'
    x = r'\s*(?:[x×]|by)\s*'
    u = r'\s*(?:cms?|in(?:\.|ch(?:es)?)?)\s*'
    unit = fr'(?P<unit>{u})?'
    unit2 = fr'(?P<unit2>{u})?'
    ou = fr'(?:{u})?'  # Optional unit, e.g. first 'cms' in '84cms x 59cms'
    dimensions = fr'{height}{ou}{x}{width}(?:{ou}{x}{depth})?{unit}(?:\({height2}{ou}{x}{width2}(?:{ou}{x}{depth2})?{unit2}\))?'
    # And we only need 2 regexes for everything!
    # Can be easily reduced to 1, but it's a matter of readability.
    return [re.compile(x, re.IGNORECASE) for x in [
        fr'^{dimensions}$',
        fr'Image:\s*{dimensions}$',  # string may also contain 'Sheet: ...', which we ignore

        # And the following regexes are for part3_scrapy
        fr'(?P<height>(?P<width>{num})){unit}diam(?:eter)?',
        # Note: further improvements include strings like:
        # - '58W x 85.5Hcm'
        # - 'height 80cm x width 100cm'
    ]]
# Building regexes at module load time is not only an optimization,
# but also makes it fail sooner rather than later on syntax errors.
REGEXES = _build_dimensions_regexes() # noqa
del _build_dimensions_regexes


ProductDimensions = namedtuple('ProductDimensions', ['height', 'width', 'depth'])
def parse_dimensions(s: str) -> ProductDimensions:
    """Returns 3-tuple of dimensions: (height, width, depth). Depth is None for flat objects."""
    s = s.strip()
    for regex in REGEXES:
        if match := regex.search(s):
            d = match.groupdict()
            # Preprocess units, should be 'in' or 'cm' without extra characters or whitespace
            for key in ('unit', 'unit2'):
                if d.get(key):
                    d[key] = d[key].strip()[:2]
            # If there are no units, assume cm
            if not d.get('unit'):
                d['unit'] = 'cm'
            # If inches are given first and cm are given second, use 'height2' etc.
            if d.get('unit2') and d['unit2'][:2] == 'cm':
                d = {k.rstrip('2'): v for k, v in d.items() if k.endswith('2')}
            unit = d['unit'][:2]
            return ProductDimensions(
                _parse_dim(d['height'], unit),
                _parse_dim(d['width'], unit),
                _parse_dim(d['depth'], unit) if d.get('depth') else None
            )
    raise ValueError(f'Failed to parse dimensions: {s}')


def _parse_dim(s: str, unit: str) -> float:
    """Parse single dimension in inches or cm, return value in cm."""
    # Convert fractions like '16 1/4'
    if match := re.match(r'(\d+)\s+(\d+)/(\d+)$', s):
        value = int(match.group(1)) + int(match.group(2)) / int(match.group(3))
    else:
        value = float(s.replace(',', '.'))  # '66,4' instead of '66.4'
    if unit[:2] == 'in':
        value = round(value * 2.54, 1)
    elif unit != 'cm':
        raise ValueError(f'Unexpected unit: {unit}')
    return value


def main():
    parse_dimensions('Sheet: 16 1/4 × 12 1/4 in. (41.3 × 31.1 cm) Image: 14 × 9 7/8 in. (35.6 × 25.1 cm)')
    dim_df = pd.read_csv("candidateEvalData/dim_df_correct.csv")
    for index, row in dim_df.iterrows():
        height, width, depth = parse_dimensions(row['rawDim'])
        if (height, width, depth) == (row['height'], row['width'], None if isnan(row['depth']) else row['depth']):
            print(f'Row {index} OK: {row["rawDim"]!r} -> {height}, {width}, {depth}')
        else:
            print(f"ERROR in row {index}: {row['rawDim']!r} -> {height!r}, {width!r}, {depth!r} vs {row['height']!r}, {row['width']!r}, {row['depth']!r}")


if __name__ == '__main__':
    main()
