from collectors.berlin_de import BerlinDeCollector


class Client:
    pass


DETAIL = '''
<html><head><meta name="description" content="A technology and business conference."></head><body>
<h1>Berlin Tech Expo</h1><dl>
<dt>Location</dt><dd>Station Berlin</dd>
<dt>Date</dt><dd>November 25 - 26, 2026</dd>
<dt>Address</dt><dd>Luckenwalder Straße 4-6 10963 Berlin</dd>
</dl></body></html>
'''


def test_parses_trade_fair_detail():
    event = BerlinDeCollector(Client(), request_delay=0)._parse_detail(
        DETAIL, "https://www.berlin.de/en/trade-fairs/123-456-berlin-tech-expo.en.html"
    )
    assert event is not None
    assert event.title == "Berlin Tech Expo"
    assert event.starts_at.year == 2026
    assert event.location == "Station Berlin, Luckenwalder Straße 4-6 10963 Berlin"
    assert event.external_id == "123-456-berlin-tech-expo"


def test_extracts_unique_detail_links():
    html = '''<a href="/en/trade-fairs/123-event.en.html">Event</a>
              <a href="/en/trade-fairs/123-event.en.html">Duplicate</a>'''
    collector = BerlinDeCollector(Client(), request_delay=0)
    assert collector._listing_links(html) == ["https://www.berlin.de/en/trade-fairs/123-event.en.html"]
