"""Single-source data publisher. Standard library only; also runs on GitHub Actions.

catalog.json is the only hand-maintained data file. Generated, revision-addressed
packs let native Shortcuts fetch just one region, one language and shared rules.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

PRODUCT = 'quick-call-image'
SCHEMA = '2'
ENGINE = '3'
BASE_URL = 'https://raw.githubusercontent.com/dammeiosvn/Clipboard-Pro-Data/main/quick-call-image/'
GROUP_HANDLERS = {
    'main': {'camera', 'photos', 'settings', 'about', 'cancel'},
    'recovery': {'camera', 'photos', 'manual', 'settings', 'cancel'},
    'results': {'manual', 'retry', 'settings', 'cancel'},
    'settings': {'country', 'language', 'restore', 'cancel'},
}
PROFILE_FIELDS = ('regionCode', 'name', 'icon', 'callingCode', 'defaultLanguage',
                  'nationalPrefix', 'acceptBareNSN', 'internationalPrefixPattern',
                  'nationalPattern', 'possibleLengths', 'numberType', 'exampleNSN',
                  'fixedExampleNSN', 'rulesRevision')
BEHAVIOR_FIELDS = ('maxInteractions', 'maxTextCharacters', 'e164Pattern',
                   'unicodeDigitPattern', 'candidatePattern', 'ignorePrefixPattern',
                   'currencySuffixPattern', 'bootstrapCountryPrompt', 'bootstrapLanguagePrompt')


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def validate(c):
    def need(ok, message):
        if not ok:
            raise ValueError(message)
    need(c['meta']['productId'] == PRODUCT, 'Wrong product')
    need(c['meta']['schemaVersion'] == SCHEMA and c['meta']['engineRevision'] == ENGINE,
         'Unsupported data schema / engine')
    for collection, order in [('countries', 'countryOrder'), ('languages', 'languageOrder')]:
        need(0 < len(c[collection]) <= 300, 'Collection size out of range: ' + collection)
        need(len(c[order]) == len(set(c[order])) and set(c[order]) == set(c[collection]),
             'Order must contain every key once: ' + order)
    need(c['defaults']['region'] in c['countries'], 'Invalid default region')
    need(c['defaults']['language'] in c['languages'], 'Invalid default language')
    need(c['defaults']['singleResult'] in ('call', 'choose'), 'Invalid call policy')
    for code, p in c['countries'].items():
        need(re.fullmatch('[A-Z]{2}', code), 'Invalid region key: ' + code)
        need(set(PROFILE_FIELDS).issubset(p), 'Incomplete profile: ' + code)
        need(p['regionCode'] == code, 'Region identity mismatch: ' + code)
        need(re.fullmatch(r'\+[1-9][0-9]{0,2}', p['callingCode']), 'Invalid calling code')
        need(p['defaultLanguage'] in c['languages'], 'Missing default language: ' + code)
        need(p['acceptBareNSN'] in ('0', '1'), 'Invalid bare-NSN flag')
        need(re.fullmatch('[0-9]*', p['nationalPrefix']), 'Invalid trunk prefix')
        need(p['numberType'] == 'FIXED_LINE_OR_MOBILE', 'Unsupported number type')
        need(isinstance(p['possibleLengths'], list) and p['possibleLengths'] and
             all(isinstance(n, int) and 5 <= n <= 15 for n in p['possibleLengths']), 'Invalid lengths')
        for key in ('nationalPattern', 'internationalPrefixPattern'):
            need(isinstance(p[key], str) and p[key].startswith(r'\A') and len(p[key]) < 20000,
                 'Invalid / oversized rule: ' + code + '/' + key)
    required = set(c['languages']['en'])
    for code, strings in c['languages'].items():
        need(re.fullmatch('[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8}){0,3}', code), 'Invalid language key: ' + code)
        need(required.issubset(strings), 'Missing translations: ' + code)
        need(all(isinstance(s, str) and s.strip() and len(s) <= 4096 for s in strings.values()),
             'Invalid / empty label: ' + code)
        for group, allowed in GROUP_HANDLERS.items():
            need(group in c['menus'], 'Missing menu: ' + group)
            seen = set()
            for item in c['menus'][group]:
                need(item['handler'] in allowed and item['enabled'] in ('0', '1'),
                     'Unsupported menu handler: ' + group)
                need(item['labelKey'] in strings and item['iconKey'] in c['icons'], 'Broken menu label / icon')
                row = c['icons'][item['iconKey']] + ' ' + strings[item['labelKey']]
                if item['enabled'] == '1':
                    need(row not in seen, 'Duplicate visible menu row: ' + code + '/' + group)
                    seen.add(row)
            need(seen, 'Empty menu: ' + group)
    need(set(BEHAVIOR_FIELDS).issubset(c['behavior']), 'Incomplete common rules')
    need(1 <= int(c['behavior']['maxInteractions']) <= 100, 'Interaction limit out of range')
    need(100 <= int(c['behavior']['maxTextCharacters']) <= 120000, 'Text limit out of range')
    need(all(re.fullmatch('[0-9]', d) for d in c['digitMap'].values()), 'Invalid digit map')


def export(c, target):
    validate(c)
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    revision = digest(compact(c))
    meta = {**c['meta'], 'revision': revision}
    index = {'meta': meta, 'defaults': c['defaults'], 'countryOrder': c['countryOrder'],
             'languageOrder': c['languageOrder'], 'countries': {}, 'languages': {}}
    outputs = {}

    def pack(kind, key, data):
        payload = compact({'meta': {**meta, 'kind': kind, 'key': key}, 'data': data})
        stem = 'core' if kind == 'core' else kind + 's/' + key
        prefix = 'packs/' + revision + '/' + stem
        # .txt is the transport form: iOS preserves its exact scalar text for
        # hashing. The .json twin is for human inspection and other clients.
        outputs[prefix + '.json'] = payload
        outputs[prefix + '.txt'] = payload
        return {'sha256': digest(payload)}

    core = {key: c[key] for key in ('meta', 'defaults', 'icons', 'menus', 'behavior', 'digitMap')}
    index['core'] = pack('core', 'core', core)
    for code in c['countryOrder']:
        profile = c['countries'][code]
        index['countries'][code] = {**{k: profile[k] for k in ('name', 'icon', 'callingCode')},
                                    **pack('region', code, profile)}
    for code in c['languageOrder']:
        index['languages'][code] = {'name': c['languages'][code]['name'],
                                    **pack('language', code, c['languages'][code])}
    outputs['index.json'] = compact(index)
    outputs['index.txt'] = outputs['index.json']
    for path, body in outputs.items():
        dest = target / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding='utf-8')
    # Keep historical revision directories: a device that fetched the previous
    # index must still be able to finish setup while a new release is published.
    return index


def active(c, region='VN', language='vi', single='call'):
    """Reference bundle used by tests/docs, not shipped as an embedded fallback."""
    return {'meta': {**c['meta'], 'revision': digest(compact(c))},
            'selection': {'region': region, 'language': language, 'singleResult': single},
            'profile': c['countries'][region], 'strings': c['languages'][language],
            'core': {k: c[k] for k in ('meta', 'defaults', 'icons', 'menus', 'behavior', 'digitMap')}}


def main():
    parser = argparse.ArgumentParser()
    base = Path(__file__).resolve().parent
    parser.add_argument('--source', type=Path, default=base / 'catalog.json')
    parser.add_argument('--out', type=Path, default=base)
    args = parser.parse_args()
    catalog = json.loads(args.source.read_text(encoding='utf-8'))
    index = export(catalog, args.out)
    print(json.dumps({'revision': index['meta']['revision'], 'countries': len(index['countries']),
                      'languages': len(index['languages']), 'indexBytes': len(compact(index).encode('utf-8'))}))


if __name__ == '__main__':
    main()
