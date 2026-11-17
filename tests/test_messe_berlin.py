from collectors.messe_berlin import MesseBerlinCollector


class Client:
    pass


def test_parses_messe_event_item():
    html = '''<div role="listitem" data-component="event-list-item">
      <div>16. - 11/18/2026</div><div>Berlin, Germany</div>
      <a href="https://example.com/esmo"><h4>ESMO AI &amp; Digital Oncology</h4></a>
      <div>Categories Technology Innovation</div><div>More info</div><div>Save appointment</div>
    </div>'''
    events = MesseBerlinCollector(Client())._parse(html)
    assert len(events) == 1
    assert events[0].title == "ESMO AI & Digital Oncology"
    assert events[0].starts_at.month == 11
    assert events[0].starts_at.day == 16
    assert events[0].location == "Berlin, Germany"


def test_ignores_non_berlin_messe_events():
    html = '''<div data-component="event-list-item"><div>06/23/2027</div><div>Singapore</div>
      <a href="https://example.com"><h4>Tech Asia</h4></a></div>'''
    assert MesseBerlinCollector(Client())._parse(html) == []
