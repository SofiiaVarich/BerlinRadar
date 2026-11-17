from collectors.websites import WebsiteCollector


class Client:
    pass


def test_json_ld_event_parser():
    html = '''<script type="application/ld+json">{
      "@type":"Event", "@id":"one", "name":"Berlin Tech Night",
      "startDate":"2027-01-10T18:30:00+01:00", "url":"https://example.com/one",
      "location":{"name":"MotionLab", "address":{"addressLocality":"Berlin"}},
      "offers":{"price":"0", "priceCurrency":"EUR"}
    }</script>'''
    events = WebsiteCollector(Client(), [])._parse(html, "https://example.com")
    assert len(events) == 1
    assert events[0].price == 0
    assert events[0].location == "MotionLab, Berlin"
