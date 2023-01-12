Setup
-----

You should have recent version of Python and pipenv.

Install dependencies using `pipenv sync` or `pipenv sync --dev` (if you want to run pytest)

All parts are implemented as Python modules, without a Jupyter notebook.

Part 1: Parsing
---------------

Module: `part1_parsing.py`

How to run:

    $ pipenv run python part1_parsing.py
       artist_name                            lot_name  price_gbp  price_usd     estimation_gbp     estimation_usd                                                                                        image_link   sale_date
    0  Peter Doig   The Architect's Home in the Ravine   11282500   16370908  10000000-15000000  14509999-21764999  http://www.christies.com/lotfinderimages/D59730/peter_doig_the_architects_home_in_the_ravine_d5973059g.jpg  2016-02-11

The python template implied that `requests` module should be used. So I run a mock web server using `http.server`,
which allows us to retrieve HTML file using GET request.

To make code nicer, I added a custom Loader class (similar to what we have in Scrapy).

Part 2: Regex
-------------

Module: `part2_regex.py`

How to run:

    $ pipenv run python part2_regex.py
    Row 0 OK: '19×52cm' -> 19.0, 52.0, None
    Row 1 OK: '50 x 66,4 cm' -> 50.0, 66.4, None
    Row 2 OK: '168.9 x 274.3 x 3.8 cm (66 1/2 x 108 x 1 1/2 in.)' -> 168.9, 274.3, 3.8
    Row 3 OK: 'Sheet: 16 1/4 × 12 1/4 in. (41.3 × 31.1 cm) Image: 14 × 9 7/8 in. (35.6 × 25.1 cm)' -> 35.6, 25.1, None
    Row 4 OK: '5 by 5in' -> 12.7, 12.7, None

I don't think writing hardcoded regexes for each string is necessary at this point, it's trivial stuff,
so I went straight implementing a general solution. Please evaluate design choices I made:
1. A list of regexes with catching groups with well-defined names, such as "height".
   Additional regexes can be added to the list at any time, without changing other code.
2. Using building blocks and templates, such as '{height}', to build regexes in a hierarchical way -
   easy to read, easy to maintain.
3. Parsing of a single dimension (such as height) is logically separated from parsing the whole expression.

Also my code supports a few more expressions found in Part 3.

There are unit tests for this part, you can run them via `pipenv run pytest`.

Part 3: Scrapy
--------------

Please see `part3_scrapy` - it contains a usual Scrapy project structure, with a single spider.

How to run:

    pipenv run scrapy runspider part3_scrapy/spiders/bearspace.py -o output.csv

You can see results in `part3_spider_output.csv`.

In settings, I did a few basic things: set User-Agent, delay, 1 request per domain, enabled caching for testing.

The spider `bearspace.py` is pretty trivial: just parse pages one by one, and extract products.
Here we can use simple yet effective technique, just adding `page=x` for page 2, 3...

For parsing of dimensions and price, I reused code from previous parts.  

I added (very basic) logging. I usually also add custom stats to the spiders, such as products count.

In item loader, I added validation - loader will raise exception and ERROR will be reported in log if items lacks title.
Other fields seem to be optional.

I also checked if it's possible to extract JSON data instead, for more efficient scraping.
It is certainly possible, but will require more time to research.
I managed to get products JSON by sending GET request with Authorization header copied from the web browser,
you can see `part3_scrapy_json_example.json`.

Part 4: SQL
-----------

Joins:
- INNER JOIN selects data that's in both tables. If left item does not have a corresponding right item, it will not be
  included, and vice versa. For example, join artists and artworks - anonymous artworks won't be included, and artists
  who don't have any artworks in the database won't be included.
- LEFT JOIN allows right item to be NULL. For example, artists LEFT JOIN artworks allows artists with 0 artworks.
- RIGHT JOIN does the opposite.
- FULL JOIN is similar to the LEFT and RIGHT, but allows any side to be NULL. In terms of set theory, it's a union of the two sets above.  

Following are not tested, and not exactly match the 4 bullet points in the instruction.
It's not entirely clear to me how many SQL queries a candidate is supposed to write.
But I hope the following code is enough. I'm not an SQL guru at all, but the task is very simple.

Join flights and airlines and add airline name to flights, while filtering only JetBlue airline: 

    SELECT arr_time, origin, dest, airlines.name AS airline_name FROM flights
    INNER JOIN airlines ON airlines.carrier=flights.carrier
    WHERE airline_name LIKE '%JetBlue%';

Total count of flights, grouped by origin, with only total counts > 10000 and sorted in ascending order.
This can be combined with INNER JOIN and/or WHERE clause above.

    SELECT origin, count(*) AS total_flights FROM flights
    GROUP BY origin
    HAVING total_flights>10000
    ORDER BY total_flights;

Time and difficulty
-------------------

All the tasks were easy, but I spent overall about 5 hours, because I willingly went over-engineering in part1 and part2,
and did some review of scraping results and subsequent improvements in part3.