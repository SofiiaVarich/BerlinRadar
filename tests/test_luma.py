import json

from collectors.luma import LumaCollector


class Client:
    pass


def test_parses_luma_item_list():
    payload = {"@type": "ItemList", "itemListElement": [{"item": {
        "@type": "Event", "@id": "https://luma.com/ai", "url": "https://luma.com/ai",
        "name": "Berlin AI Meetup", "startDate": "2026-11-25T18:30:00+01:00",
        "location": {"name": "Merantix AI Campus", "address": {"addressLocality": "Berlin"}},
        "offers": [{"price": 0, "priceCurrency": "eur"}],
    }}]}
    html = f'<script type="application/ld+json">{json.dumps(payload)}</script>'
    events = LumaCollector(Client())._parse(html)
    assert len(events) == 1
    assert events[0].title == "Berlin AI Meetup"
    assert events[0].location == "Merantix AI Campus, Berlin"
    assert events[0].price == 0
    assert events[0].currency == "EUR"
