"""Native AppList Pro compiler: direct launch menu, no browser or runtime code downloads."""
from pathlib import Path
import hashlib
import json
import plistlib

from catalog import BASE_URL, VERSION, DATA_VERSION, KEYS, publish
from workflow import Workflow, dictionary_value, variable as v, ref, token

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = '4'
ACTIVE = 'apps.v4.json'
PREVIOUS = 'apps.previous.v4.json'
PENDING = 'apps.pending.v4.json'
LABELS = 'labels.v4.json'
TITLE = 'AppList Pro · © Sentechtipsvn'
FOLDER = {'fileLocation': {'WFFileLocationType': 'Shortcuts', 'relativeSubpath': '',
    'appContainerBundleIdentifier': 'com.apple.shortcuts',
    'fileProviderDomainID': 'com.apple.CloudDocs.MobileDocumentsFileProvider'},
    'filename': 'Documents', 'displayName': 'Shortcuts'}
JS = r'"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"'
PAIR = JS + r'\s*:\s*' + JS
FLAT = r'\{\s*(?:' + PAIR + r'(?:\s*,\s*' + PAIR + r')*)?\s*\}'
FLAT_PATTERN = r'\A\s*' + FLAT + r'\s*\z'
PIN_PAIR = JS + r'\s*:\s*(?:' + JS + r'|[01])'
PIN_MAP = r'\{\s*(?:' + PIN_PAIR + r'(?:\s*,\s*' + PIN_PAIR + r')*)?\s*\}'
BUNDLE = r'\A[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\z'
NAME = r'\A(?![⭐⚙↩])[^\x00-\x1f\x7f\r\n]{1,90}\z'
STORE = r'\Ahttps://apps\.apple\.com/(?:[^\s/#?]+/)*id[0-9]+(?:\?[^\s#]*)?(?:#[^\s]*)?\z'


def object_pattern(keys):
    # Limit keys before using Get Dictionary Value. Exactly N distinct keys
    # after parsing implies every required key is present, in any order.
    field = r'"(?:' + '|'.join(keys) + r')"\s*:\s*' + JS
    return r'\A\s*\{\s*' + field + r'(?:\s*,\s*' + field + r'){' + str(len(keys) - 1) + r'}\s*\}\s*\z'


STATE_PATTERN = object_pattern(('product', 'schema', 'language', 'revision',
    'namesJSON', 'bundlesJSON', 'storesJSON', 'pinsJSON'))
LABEL_PATTERN = object_pattern((*KEYS, '_locale', '_dataVersion'))


def build():
    descriptors = publish()
    catalog = json.loads((ROOT / 'config/strings.json').read_text())
    boot = {'name': 'AppList Pro', 'title': TITLE, 'author': '© Sentechtipsvn',
            'version': VERSION, 'baseURL': BASE_URL, 'languages': descriptors,
            'fallback': catalog['en'], 'dataVersion': DATA_VERSION, 'values': {}}
    w = Workflow('AppList Pro')
    a, get, text, put, L = w.action, w.get, w.text, w.put, w.label

    def exists_key(source, key):
        # iOS 18 renders beta2's array-typed Contains with a missing RHS.
        # IDs in these maps are SHA-256 hex values. Combine explicitly and
        # match a whole quoted line instead of using an array predicate.
        keys = w.keys(source)
        w.set('KeyMatchCount', w.count(keys))
        populated = w.if_gt(v('KeyMatchCount'))
        lines = a('text.combine', {'text': ref(keys), 'WFTextSeparator': 'New Lines'}, 'Stored app IDs')
        w.set('KeyMatchCount', w.count(w.match(lines, r'(?m)^\Q', key, r'\E$')))
        w.end_if(populated)
        return w.if_gt(v('KeyMatchCount'))

    def check(value, expected, message='invalidData', code=None):
        group = w.if_eq(value, expected)
        w.otherwise(group)
        w.alert(text(L(message), '\n\n', code) if code else L(message), stop=True, title=TITLE)
        w.end_if(group)

    def read(name):
        return a('documentpicker.open', {'WFFile': ref(v('StorageRoot')),
            'WFGetFilePath': token('AppListPro/', name) if isinstance(name, dict) else 'AppListPro/' + name, 'WFFileErrorIfNotFound': False,
            'WFGetFolderContents': False}, 'Read local JSON')

    def save(body, name):
        # Save the Dictionary itself, as in the user's original export. The
        # native file action owns JSON encoding, filename and escaping.
        return a('documentpicker.save', {'WFInput': ref(body), 'WFFolder': ref(v('StorageRoot')),
            'WFAskWhereToSave': False, 'WFFileDestinationPath': token('AppListPro/', name) if isinstance(name, dict) else 'AppListPro/' + name,
            'WFSaveFileOverwrite': True}, 'Save local JSON')

    def scalar_check(value, expected, message='saveFailed', code=None):
        # A nonempty prefix also makes an empty Store URL a valid If operand.
        check(text('value:', value), text('value:', expected), message, code)

    def candidate(source):
        """Read a flat native JSON file; map JSON is encoded by iOS, not by us."""
        w.assign('CandidateOK', '0')
        raw = a('detect.text', {'WFInput': ref(source)}, 'Read state file contents')
        guards = [w.if_match(raw, STATE_PATTERN)]
        data = a('detect.dictionary', {'WFInput': ref(raw)}, 'Native app state')
        guards.append(w.if_eq(w.count(w.keys(data)), '8'))
        for key, expected in [('product', 'applist-pro'), ('schema', SCHEMA)]:
            guards.append(w.if_eq(get(data, key), expected))
        lang = text(get(data, 'language'))
        guards.append(w.if_match(lang, r'\A(?:' + '|'.join(descriptors) + r')\z'))
        revision = text(get(data, 'revision'))
        guards.append(w.if_match(revision, r'\A[0-9a-f]{64}\z'))
        maps = {}
        for collection in ('Names', 'Bundles', 'Stores', 'Pins'):
            body = text(get(data, collection.lower() + 'JSON'))
            pattern = r'\A\s*' + PIN_MAP + r'\s*\z' if collection == 'Pins' else FLAT_PATTERN
            guards.append(w.if_match(body, pattern))
            maps[collection] = a('detect.dictionary', {'WFInput': ref(body)}, 'Read ' + collection)
        count = w.count(w.keys(maps['Names']))
        for collection in ('Bundles', 'Stores', 'Pins'):
            guards.append(w.if_eq(w.count(w.keys(maps[collection])), count))
        w.set('Candidate', data)
        w.set('CandidateEnvelope', data)
        w.set('CandidateDigest', revision)
        for collection, mapping in maps.items():
            w.set('Candidate' + collection, mapping)
        w.assign('CandidateOK', '1')
        for group in reversed(guards):
            w.end_if(group)

    def bind():
        w.set('Language', get(v('Candidate'), 'language'))
        for collection in ('Names', 'Bundles', 'Stores', 'Pins'):
            w.set(collection, v('Candidate' + collection))
        w.assign('LanguageReady', '1')

    def labels_candidate(source, language):
        w.assign('LabelsOK', '0')
        raw = a('detect.text', {'WFInput': ref(source)}, 'Read language file contents')
        guards = [w.if_match(raw, LABEL_PATTERN)]
        labels = a('detect.dictionary', {'WFInput': ref(raw)}, 'Cached language dictionary')
        guards.append(w.if_eq(w.count(w.keys(labels)), str(len(KEYS) + 2)))
        guards.append(w.if_eq(get(labels, '_locale'), language))
        guards.append(w.if_eq(get(labels, '_dataVersion'), get(v('Config'), 'dataVersion')))
        w.assign('LabelKeysOK', '1')
        loop, key = w.each(w.keys(get(v('Config'), 'fallback')))
        present = w.if_text(text(get(labels, key)))
        w.otherwise(present)
        w.assign('LabelKeysOK', '0')
        w.end_if(present)
        w.end_loop(loop)
        guards.append(w.if_eq(v('LabelKeysOK'), '1'))
        w.set('CachedStrings', labels)
        w.assign('LabelsOK', '1')
        for group in reversed(guards):
            w.end_if(group)

    def load_labels():
        # A damaged or mismatched UI cache must not block the app launcher.
        w.set('Strings', get(v('Config'), 'fallback'))
        labels_candidate(read(LABELS), v('Language'))
        good = w.if_eq(v('LabelsOK'), '1')
        w.set('Strings', v('CachedStrings'))
        w.otherwise(good)
        labels_candidate(read('labels.previous.v4.json'), v('Language'))
        previous = w.if_eq(v('LabelsOK'), '1')
        w.set('Strings', v('CachedStrings'))
        w.end_if(previous)
        w.end_if(good)

    def ensure_unchanged():
        known = w.if_match(v('DiskDigest'), r'\A[0-9a-f]{64}\z')
        raw = a('detect.text', {'WFInput': ref(read(ACTIVE))}, 'Read current revision')
        valid = w.if_match(raw, STATE_PATTERN)
        w.otherwise(valid)
        w.alert(L('changedElsewhere'), stop=True, title=TITLE)
        w.end_if(valid)
        data = a('detect.dictionary', {'WFInput': ref(raw)}, 'Current revision metadata')
        check(w.count(w.keys(data)), '8', 'changedElsewhere')
        scalar_check(get(data, 'revision'), v('DiskDigest'), 'changedElsewhere')
        w.end_if(known)

    def persist():
        fields = {'product': 'applist-pro', 'schema': SCHEMA, 'language': v('Language')}
        for collection in ('Names', 'Bundles', 'Stores', 'Pins'):
            # Empty Dictionary -> Text can be absent on iOS. Use an explicit
            # native string for this one special case.
            w.assign(collection + 'JSON', '{}')
            populated = w.if_has(w.keys(v(collection)))
            w.set(collection + 'JSON', text(v(collection)))
            w.end_if(populated)
            fields[collection.lower() + 'JSON'] = v(collection + 'JSON')
        # Opaque revision generated once, stored and compared as text. This is
        # a concurrency token, not a hash of the file's JSON serialization.
        w.set('NewDigest', w.hash(text(v('NamesJSON'), v('BundlesJSON'),
            v('StoresJSON'), v('PinsJSON'), v('Language'), v('ActiveDigest'))))
        fields['revision'] = v('NewDigest')
        env = a('dictionary', {'WFItems': dictionary_value(fields)}, 'New native state dictionary')
        ensure_unchanged()
        a('file.createfolder', {'WFFolder': ref(v('StorageRoot')), 'WFFilePath': 'AppListPro'})
        old = w.if_eq(v('ActiveValid'), '1')
        w.otherwise(old)
        unreadable = read(ACTIVE)
        has_unreadable = w.if_has(unreadable)
        save(unreadable, 'unreadable-before-reset.v4.json')
        w.end_if(has_unreadable)
        w.end_if(old)
        # One native validation block serves each of the three writes. Order
        # is staged data -> previous known state -> current data.
        files = a('list', {'WFItems': [{'WFItemType': 0, 'WFValue': token(name)}
                    for name in (PENDING, PREVIOUS, ACTIVE)]}, 'Write order')
        loop, filename = w.each(files)
        w.set('WriteName', filename)
        w.set('WriteBody', env)
        w.set('ExpectedRevision', v('NewDigest'))
        w.assign('VerifyContents', '1')
        w.assign('WriteThis', '1')
        previous = w.if_eq(v('WriteName'), PREVIOUS)
        available = w.if_eq(v('ActiveValid'), '1')
        w.set('WriteBody', v('ActiveEnvelope'))
        w.set('ExpectedRevision', v('ActiveDigest'))
        w.assign('VerifyContents', '0')
        w.otherwise(available)
        w.assign('WriteThis', '0')
        w.end_if(available)
        w.end_if(previous)
        write_this = w.if_eq(v('WriteThis'), '1')
        final_write = w.if_eq(v('WriteName'), ACTIVE)
        ensure_unchanged()
        w.end_if(final_write)
        save(v('WriteBody'), v('WriteName'))
        candidate(read(v('WriteName')))
        code = text('AP4 / ', v('WriteName'))
        check(v('CandidateOK'), '1', 'saveFailed', code)
        scalar_check(v('CandidateDigest'), v('ExpectedRevision'), code=code)
        contents = w.if_eq(v('VerifyContents'), '1')
        records, identifier = w.each(w.keys(v('Names')))
        for collection in ('Names', 'Bundles', 'Stores', 'Pins'):
            scalar_check(get(v('Candidate' + collection), identifier),
                         get(v(collection), identifier), code=code)
        w.end_loop(records)
        for collection in ('Names', 'Bundles', 'Stores', 'Pins'):
            scalar_check(w.count(w.keys(v('Candidate' + collection))),
                         w.count(w.keys(v(collection))), code=code)
        scalar_check(get(v('Candidate'), 'language'), v('Language'), code=code)
        w.end_if(contents)
        w.end_if(write_this)
        w.end_loop(loop)
        w.set('ActiveEnvelope', env)
        w.set('ActiveDigest', v('NewDigest'))
        w.set('DiskDigest', v('NewDigest'))
        w.assign('ActiveValid', '1')

    def request_save(message='saved', after='main'):
        w.assign('SaveMessage', message)
        w.assign('AfterSave', after)
        w.assign('Route', 'save')

    def start_menu():
        w.empty_list('Rows')
        w.empty_dict('RowMap')

    def row(display, identifier):
        w.append('Rows', display)
        w.set('RowMap', put(v('RowMap'), w.hash(display), identifier))

    def finish(prompt):
        selected = text(w.choose(v('Rows'), prompt), name='Chosen label')
        return text(get(v('RowMap'), w.hash(selected)), name='Chosen stable ID')

    def menu(items, prompt=TITLE):
        fields, rows = [], []
        for icon, key, handler in items:
            display = token(icon, ' ', L(key))
            fields.append({'WFItemType': 0, 'WFKey': display, 'WFValue': token(handler)})
            rows.append({'WFItemType': 0, 'WFValue': display})
        mapping = a('dictionary', {'WFItems': {'Value': {'WFDictionaryFieldValueItems': fields},
                    'WFSerializationType': 'WFDictionaryFieldValue'}}, 'Menu routes')
        w.set('FixedMenuMap', mapping)
        options = a('list', {'WFItems': rows}, 'Menu labels')
        selected = text(w.choose(options, prompt), name='Chosen menu label')
        return text(get(mapping, selected), name='Chosen menu route')

    def app_rows(back=False):
        start_menu()
        w.empty_list('PinnedRows')
        w.empty_list('OtherRows')
        loop, app_id = w.each(w.keys(v('Names')))
        w.set('DisplayRow', get(v('Names'), app_id))
        pinned = w.if_eq(get(v('Pins'), app_id), '1')
        w.set('DisplayRow', text('⭐ ', v('DisplayRow')))
        w.append('PinnedRows', v('DisplayRow'))
        w.otherwise(pinned)
        w.append('OtherRows', v('DisplayRow'))
        w.end_if(pinned)
        w.set('RowMap', put(v('RowMap'), w.hash(v('DisplayRow')), app_id))
        w.end_loop(loop)
        populated = w.if_has(w.keys(v('Names')))
        sorted_groups = [a('filter.files', {'WFContentItemInputParameter': ref(v(source)),
            'WFContentItemSortOrder': 'A to Z', 'WFContentItemSortProperty': 'Name'}, 'Sorted app names')
            for source in ('PinnedRows', 'OtherRows')]
        lines = w.replace(text(sorted_groups[0], '\n', sorted_groups[1]), r'\A\s+|\s+\z', '')
        w.set('Rows', a('text.split', {'text': token(lines), 'WFTextSeparator': 'New Lines'}, 'App rows'))
        w.end_if(populated)
        if back:
            row(text('↩️ ', L('back')), text('back'))

    def choose_language():
        start_menu()
        loop, code = w.each(w.keys(get(v('Config'), 'languages')))
        row(get(get(get(v('Config'), 'languages'), code), 'name'), code)
        w.end_loop(loop)
        w.set('NewLanguage', finish(text('🌐 ', L('language'))))

    def fetch_language():
        # Fetch the readable JSON already published in the same repository.
        url = text(get(v('Config'), 'baseURL'), v('NewLanguage'), '.json')
        response = a('downloadurl', {'WFURL': token(url), 'WFHTTPMethod': 'GET'}, 'Download selected language only')
        raw = text(response)
        good = w.if_match(raw, object_pattern(KEYS))
        w.otherwise(good)
        w.alert(L('invalidData'), stop=True, title=TITLE)
        w.end_if(good)
        labels = a('detect.dictionary', {'WFInput': ref(raw)}, 'Selected language')
        check(w.count(w.keys(labels)), str(len(KEYS)))
        labels = put(labels, text('_locale'), v('NewLanguage'))
        labels = put(labels, text('_dataVersion'), get(v('Config'), 'dataVersion'))
        w.set('NextStrings', labels)
        a('file.createfolder', {'WFFolder': ref(v('StorageRoot')), 'WFFilePath': 'AppListPro'})
        save(v('NextStrings'), 'labels.pending.v4.json')
        labels_candidate(read('labels.pending.v4.json'), v('NewLanguage'))
        check(v('LabelsOK'), '1', 'saveFailed', 'AP410')
        old_labels = read(LABELS)
        old = w.if_has(old_labels)
        save(old_labels, 'labels.previous.v4.json')
        w.end_if(old)
        save(v('NextStrings'), LABELS)
        labels_candidate(read(LABELS), v('NewLanguage'))
        check(v('LabelsOK'), '1', 'saveFailed', 'AP411')
        w.set('Language', v('NewLanguage'))
        w.set('Strings', v('CachedStrings'))
        w.assign('LanguageReady', '1')

    def name_check(name, current_id):
        w.assign('NameOK', '0')
        good = w.if_match(name, NAME)
        w.assign('NameOK', '1')
        loop, item = w.each(w.keys(v('Names')))
        same = w.if_eq(item, current_id)
        w.otherwise(same)
        same_name = w.if_eq(get(v('Names'), item), name)
        w.assign('NameOK', '0')
        w.end_if(same_name)
        w.end_if(same)
        w.end_loop(loop)
        w.end_if(good)

    def commit_app():
        w.set('Names', put(v('Names'), v('EditID'), v('EditName')))
        w.set('Bundles', put(v('Bundles'), v('EditID'), v('EditBundle')))
        w.set('Stores', put(v('Stores'), v('EditID'), v('EditStore')))
        w.set('Pins', put(v('Pins'), v('EditID'), v('EditPin')))
        request_save()

    def ask(prompt, default=None):
        params = {'WFAskActionPrompt': token(prompt), 'WFInputType': 'Text', 'WFAllowsMultilineText': False}
        if default is not None:
            params['WFAskActionDefaultAnswer'] = token(default)
        return text(a('ask', params, 'User input'))

    def search_app():
        query = w.replace(ask(L('searchPrompt')), r'\A\s+|\s+\z', '')
        w.assign('AppFound', '0')
        supplied = w.if_text(query)
        results = a('searchappstore', {'WFSearchTerm': token(query)}, 'App Store results')
        has_results = w.if_has(results)
        selected = w.choose(results, L('chooseApp'))
        w.set('EditName', text(a('properties.appstore', {
            'WFInput': ref(selected), 'WFContentItemPropertyName': 'Name'}, 'App name')))
        w.set('EditBundle', text(a('properties.appstore', {'WFInput': ref(selected),
            'WFContentItemPropertyName': 'Bundle Identifier'}, 'App bundle ID')))
        w.set('EditStore', text(a('properties.appstore', {'WFInput': ref(selected),
            'WFContentItemPropertyName': 'Store URL'}, 'App Store URL')))
        w.assign('AppFound', '1')
        w.end_if(has_results)
        w.end_if(supplied)

    def lookup_link(link):
        w.assign('AppFound', '0')
        correct = w.if_match(link, STORE)
        appid = w.first(w.match(link, r'(?<=/id)[0-9]+'))
        w.assign('Storefront', 'us')
        countries = w.match(link, r'(?<=apps\.apple\.com/)[a-z]{2}(?=/)')
        has_country = w.if_has(countries)
        w.set('Storefront', w.first(countries))
        w.end_if(has_country)
        url = text('https://itunes.apple.com/lookup?id=', appid, '&country=', v('Storefront'))
        response = a('downloadurl', {'WFURL': token(url), 'WFHTTPMethod': 'GET'}, 'Look up public App Store metadata')
        data = a('detect.dictionary', {'WFInput': ref(response)}, 'Apple lookup response')
        records = get(data, 'results')
        found = w.if_has(records)
        app = w.first(records)
        valid = w.if_match(get(app, 'bundleId'), BUNDLE)
        w.set('EditName', text(get(app, 'trackName')))
        w.set('EditBundle', text(get(app, 'bundleId')))
        w.set('EditStore', text(get(app, 'trackViewUrl')))
        w.assign('AppFound', '1')
        w.end_if(valid)
        w.end_if(found)
        w.end_if(correct)

    def validate_import():
        """Expensive semantic validation is confined to imports, not every launch."""
        w.assign('ImportOK', '1')
        w.empty_dict('ImportNamesSeen')
        names = v('CandidateNames')
        loop, identifier = w.each(w.keys(names))
        w.set('ImportID', identifier)
        guards = [w.if_match(identifier, r'\A[0-9a-f]{64}\z')]
        for field in ('bundles', 'stores', 'pins'):
            guards.append(exists_key(v('Candidate' + field.title()), identifier))
        bundle = text(get(v('CandidateBundles'), identifier))
        name = text(get(names, identifier))
        guards.append(w.if_match(bundle, BUNDLE))
        guards.append(w.if_eq(w.hash(bundle), identifier))
        guards.append(w.if_match(name, NAME))
        guards.append(w.if_match(get(v('CandidatePins'), identifier), r'\A[01]\z'))
        guards.append(w.if_match(get(v('CandidateStores'), identifier), r'\A\z|' + STORE))
        duplicate = exists_key(v('ImportNamesSeen'), w.hash(name))
        w.assign('ImportOK', '0')
        w.end_if(duplicate)
        w.set('ImportNamesSeen', put(v('ImportNamesSeen'), w.hash(name), '1'))
        for group in reversed(guards):
            w.otherwise(group)
            w.assign('ImportOK', '0')
            w.end_if(group)
        w.end_loop(loop)

    resources = a('dictionary', {'WFItems': dictionary_value(boot)}, 'AppList Pro configuration')
    top_index = len(w.actions) - 1
    w.set('Config', resources)
    w.set('Constants', get(v('Config'), 'values'))
    w.assign('EmptyText', '')
    w.enable_constants('Constants', 'EmptyText')
    w.set('Strings', get(v('Config'), 'fallback'))
    w.set('StorageRoot', a('file', {'WFFile': FOLDER}, 'Portable iCloud Shortcuts folder'))
    for var in ('ActiveDigest', 'ActiveEnvelope', 'DiskDigest', 'Language', 'SharedLink'):
        w.assign(var, '0')
    for var in ('Names', 'Bundles', 'Stores', 'Pins'):
        w.empty_dict(var)
    w.assign('ActiveValid', '0')
    w.assign('LanguageReady', '0')
    w.assign('PendingImport', '0')
    w.assign('Route', 'configure')
    w.assign('Recovered', '0')
    active_file = read(ACTIVE)
    candidate(active_file)
    ready = w.if_eq(v('CandidateOK'), '1')
    w.set('ActiveEnvelope', v('CandidateEnvelope'))
    w.set('ActiveDigest', v('CandidateDigest'))
    w.set('DiskDigest', v('CandidateDigest'))
    w.assign('ActiveValid', '1')
    w.otherwise(ready)
    previous_file = read(PREVIOUS)
    candidate(previous_file)
    previous = w.if_eq(v('CandidateOK'), '1')
    w.set('ActiveEnvelope', v('CandidateEnvelope'))
    w.set('ActiveDigest', v('CandidateDigest'))
    w.assign('ActiveValid', '1')
    w.assign('Recovered', '1')
    w.otherwise(previous)
    some_file = w.if_text(text(active_file, previous_file))
    w.alert(L('invalidData'), title=TITLE)
    w.assign('Route', 'recover')
    w.end_if(some_file)
    w.end_if(previous)
    w.end_if(ready)
    loaded = w.if_eq(v('ActiveValid'), '1')
    bind()
    load_labels()
    w.assign('Route', 'main')
    recovered = w.if_eq(v('Recovered'), '1')
    w.alert(L('recovered'), title=TITLE)
    w.end_if(recovered)
    w.end_if(loaded)
    # Only process incoming content when explicitly launched from a share sheet.
    incoming = {'Type': 'ExtensionInput'}
    shared = w.if_has(incoming)
    urls = a('detect.link', {'WFInput': ref(incoming)}, 'Shared URLs')
    has_url = w.if_has(urls)
    w.set('SharedLink', text(w.first(urls)))
    shared_valid = w.if_match(v('SharedLink'), STORE)
    loaded = w.if_eq(v('ActiveValid'), '1')
    w.assign('Route', 'shared')
    w.end_if(loaded)
    w.otherwise(shared_valid)
    w.assign('SharedLink', '')
    w.end_if(shared_valid)
    w.end_if(has_url)
    w.end_if(shared)

    interactions = w.times(60)
    w.set('PassRoute', v('Route'))
    setup = w.if_eq(v('PassRoute'), 'configure')
    choose_language()
    w.assign('LanguageSaveMessage', '')
    w.assign('Route', 'fetchLanguage')
    w.end_if(setup)

    recovery = w.if_eq(v('PassRoute'), 'recover')
    start_menu()
    row(text('📂 ', L('import')), text('import'))
    row(text('🆕 New list / Danh sách mới'), text('configure'))
    row(text('✖ ', L('cancel')), text('cancel'))
    w.set('Route', finish(text(TITLE)))
    w.end_if(recovery)

    main = w.if_eq(v('PassRoute'), 'main')
    app_rows()
    empty = w.if_eq(w.count(w.keys(v('Names'))), '0')
    row(text('➕ ', L('add')), text('add'))
    w.end_if(empty)
    row(text('⚙️ ', L('manage')), text('manage'))
    chosen = finish(text(TITLE))
    app = w.if_match(chosen, r'\A[0-9a-f]{64}\z')
    bundle = get(v('Bundles'), chosen)
    valid_bundle = w.if_match(bundle, BUNDLE)
    a('openapp', {'WFSelectedApp': ref(bundle)}, 'Open chosen app directly')
    a('exit')
    w.otherwise(valid_bundle)
    w.alert(L('invalidData'), title=TITLE)
    w.end_if(valid_bundle)
    w.otherwise(app)
    w.set('Route', chosen)
    w.end_if(app)
    w.end_if(main)

    manage = w.if_eq(v('PassRoute'), 'manage')
    w.set('Route', menu([('➕', 'add', 'add'), ('✏️', 'edit', 'pickEdit'), ('🗑️', 'delete', 'pickDelete'),
        ('🛍️', 'store', 'store'), ('🌐', 'language', 'language'), ('💾', 'backups', 'backups'),
        ('ℹ️', 'info', 'info'), ('↩️', 'back', 'main')]))
    w.end_if(manage)

    adding = w.if_match(v('PassRoute'), r'\A(?:add|shared)\z')
    w.assign('AddMode', 'link')
    ordinary = w.if_eq(v('PassRoute'), 'add')
    w.set('AddMode', menu([('🔎', 'search', 'search'), ('🔗', 'paste', 'link'), ('↩️', 'back', 'back')]))
    w.end_if(ordinary)
    w.assign('AppFound', '0')
    searching = w.if_eq(v('AddMode'), 'search')
    search_app()
    w.end_if(searching)
    link_mode = w.if_eq(v('AddMode'), 'link')
    ordinary = w.if_eq(v('PassRoute'), 'add')
    w.set('SharedLink', ask(L('linkPrompt')))
    w.end_if(ordinary)
    lookup_link(v('SharedLink'))
    w.assign('SharedLink', '')
    w.end_if(link_mode)
    found = w.if_eq(v('AppFound'), '1')
    valid = w.if_match(v('EditBundle'), BUNDLE)
    w.set('EditID', w.hash(v('EditBundle')))
    w.assign('EditPin', '0')
    duplicate = exists_key(v('Names'), v('EditID'))
    w.alert(L('exists'), title=TITLE)
    w.assign('Route', 'main')
    w.otherwise(duplicate)
    w.set('EditName', w.replace(v('EditName'), r'\A\s+|\s+\z', ''))
    name_check(v('EditName'), v('EditID'))
    good_name = w.if_eq(v('NameOK'), '1')
    commit_app()
    w.otherwise(good_name)
    w.assign('Route', 'rename')
    w.end_if(good_name)
    w.end_if(duplicate)
    w.otherwise(valid)
    w.alert(L('invalidData'), title=TITLE)
    w.assign('Route', 'manage')
    w.end_if(valid)
    w.otherwise(found)
    back = w.if_eq(v('AddMode'), 'back')
    w.otherwise(back)
    w.alert(L('noResults'), title=TITLE)
    w.end_if(back)
    w.assign('Route', 'manage')
    w.end_if(found)
    w.end_if(adding)

    picking = w.if_match(v('PassRoute'), r'\A(?:pickEdit|pickDelete)\z')
    any_apps = w.if_has(w.keys(v('Names')))
    app_rows(back=True)
    choice = finish(L('chooseApp'))
    picked = w.if_match(choice, r'\A[0-9a-f]{64}\z')
    w.set('EditID', choice)
    for var, source in [('EditName', 'Names'), ('EditBundle', 'Bundles'), ('EditStore', 'Stores'), ('EditPin', 'Pins')]:
        w.set(var, get(v(source), v('EditID')))
    deleting = w.if_eq(v('PassRoute'), 'pickDelete')
    w.assign('Route', 'delete')
    w.otherwise(deleting)
    w.assign('Route', 'edit')
    w.end_if(deleting)
    w.otherwise(picked)
    w.assign('Route', 'manage')
    w.end_if(picked)
    w.otherwise(any_apps)
    w.alert(L('empty'), title=TITLE)
    w.assign('Route', 'manage')
    w.end_if(any_apps)
    w.end_if(picking)

    editing = w.if_eq(v('PassRoute'), 'edit')
    w.assign('PinLabel', 'pin')
    is_pinned = w.if_eq(v('EditPin'), '1')
    w.assign('PinLabel', 'unpin')
    w.end_if(is_pinned)
    start_menu()
    row(text('✏️ ', L('rename')), text('rename'))
    row(text('⭐ ', get(v('Strings'), v('PinLabel'))), text('pin'))
    row(text('🛍️ ', L('store')), text('itemStore'))
    row(text('🗑️ ', L('delete')), text('delete'))
    row(text('↩️ ', L('back')), text('manage'))
    w.set('Route', finish(v('EditName')))
    w.end_if(editing)

    renaming = w.if_eq(v('PassRoute'), 'rename')
    w.set('EditName', w.replace(ask(L('namePrompt'), v('EditName')), r'\A\s+|\s+\z', ''))
    name_check(v('EditName'), v('EditID'))
    good = w.if_eq(v('NameOK'), '1')
    commit_app()
    w.otherwise(good)
    w.alert(L('badName'), title=TITLE)
    w.end_if(good)
    w.end_if(renaming)

    pinning = w.if_eq(v('PassRoute'), 'pin')
    pinned = w.if_eq(v('EditPin'), '1')
    w.assign('EditPin', '0')
    w.otherwise(pinned)
    w.assign('EditPin', '1')
    w.end_if(pinned)
    commit_app()
    w.end_if(pinning)

    deleting = w.if_eq(v('PassRoute'), 'delete')
    confirmed = menu([('🗑️', 'delete', 'confirm'), ('↩️', 'back', 'back')], text(L('deleteConfirm'), '\n\n', v('EditName')))
    yes = w.if_eq(confirmed, 'confirm')
    for name in ('Names', 'Bundles', 'Stores', 'Pins'):
        w.empty_dict('New' + name)
    loop, identifier = w.each(w.keys(v('Names')))
    selected = w.if_eq(identifier, v('EditID'))
    w.otherwise(selected)
    for name in ('Names', 'Bundles', 'Stores', 'Pins'):
        w.set('New' + name, put(v('New' + name), identifier, get(v(name), identifier)))
    w.end_if(selected)
    w.end_loop(loop)
    for name in ('Names', 'Bundles', 'Stores', 'Pins'):
        w.set(name, v('New' + name))
    request_save(message='removed')
    w.otherwise(yes)
    w.assign('Route', 'manage')
    w.end_if(yes)
    w.end_if(deleting)

    for route in ('store', 'itemStore'):
        opening_store = w.if_eq(v('PassRoute'), route)
        if route == 'store':
            search_app()
            found = w.if_eq(v('AppFound'), '1')
        else:
            found = w.if_match(v('EditStore'), STORE)
        good_url = w.if_match(v('EditStore'), STORE)
        a('openurl', {'WFInput': ref(v('EditStore'))}, 'Open App Store page')
        a('exit')
        w.end_if(good_url)
        w.otherwise(found)
        w.alert(L('noResults' if route == 'store' else 'missingStore'), title=TITLE)
        w.end_if(found)
        w.assign('Route', 'manage')
        w.end_if(opening_store)

    lang = w.if_eq(v('PassRoute'), 'language')
    choose_language()
    w.assign('LanguageSaveMessage', '')
    w.assign('Route', 'fetchLanguage')
    w.end_if(lang)
    reload_lang = w.if_eq(v('PassRoute'), 'reload')
    w.set('NewLanguage', v('Language'))
    w.assign('LanguageSaveMessage', 'saved')
    w.assign('Route', 'fetchLanguage')
    w.end_if(reload_lang)
    fetch = w.if_eq(v('PassRoute'), 'fetchLanguage')
    fetch_language()
    pending_import = w.if_eq(v('PendingImport'), '1')
    # Selecting a language for a pending import never writes an empty app list.
    w.assign('Route', 'importReady')
    w.otherwise(pending_import)
    request_save(message='')
    w.set('SaveMessage', v('LanguageSaveMessage'))
    pending = w.if_match(v('SharedLink'), STORE)
    w.assign('AfterSave', 'shared')
    w.end_if(pending)
    w.end_if(pending_import)
    w.end_if(fetch)

    backups = w.if_eq(v('PassRoute'), 'backups')
    w.set('Route', menu([('📤', 'export', 'export'), ('📂', 'import', 'import'),
        ('↶', 'restore', 'restore'), ('🔄', 'update', 'reload'), ('↩️', 'back', 'manage')]))
    w.end_if(backups)
    export = w.if_eq(v('PassRoute'), 'export')
    file = w.named_json(text(v('ActiveEnvelope')), 'AppListPro-backup.json')
    a('documentpicker.save', {'WFInput': ref(file), 'WFAskWhereToSave': True,
        'WFSaveFileOverwrite': False}, 'Export private backup')
    w.assign('Route', 'backups')
    w.end_if(export)

    importing = w.if_match(v('PassRoute'), r'\A(?:import|restore|importReady)\z')
    w.assign('ImportReturn', 'recover')
    current_list = w.if_eq(v('ActiveValid'), '1')
    w.assign('ImportReturn', 'backups')
    w.end_if(current_list)
    resumed_import = w.if_eq(v('PassRoute'), 'importReady')
    w.otherwise(resumed_import)
    restoration = w.if_eq(v('PassRoute'), 'restore')
    w.set('ImportText', text(read(PREVIOUS)))
    w.otherwise(restoration)
    selected_file = a('file.select', {'SelectMultiple': False}, 'Choose backup or legacy JSON')
    selected_text = a('detect.text', {'WFInput': ref(selected_file)}, 'Read selected JSON contents')
    w.set('ImportText', w.replace(text(selected_text), r'\A\uFEFF', ''))
    w.end_if(restoration)
    w.end_if(resumed_import)
    w.assign('PendingImport', '0')
    candidate(v('ImportText'))
    modern = w.if_eq(v('CandidateOK'), '1')
    validate_import()
    valid = w.if_eq(v('ImportOK'), '1')
    confirmed = menu([('✅', 'import', 'confirm'), ('↩️', 'back', 'back')], L('replaceConfirm'))
    yes = w.if_eq(confirmed, 'confirm')
    bind()
    load_labels()
    request_save()
    w.otherwise(yes)
    w.set('Route', v('ImportReturn'))
    w.end_if(yes)
    w.otherwise(valid)
    w.alert(L('invalidData'), title=TITLE)
    w.set('Route', v('ImportReturn'))
    w.end_if(valid)
    w.otherwise(modern)
    # Legacy format: {displayName: bundleID}. Preserve the original file.
    flat = w.if_match(v('ImportText'), FLAT_PATTERN)
    configured = w.if_eq(v('LanguageReady'), '1')
    legacy = a('detect.dictionary', {'WFInput': ref(v('ImportText'))}, 'Legacy app list')
    for var in ('LegacyNames', 'LegacyBundles', 'LegacyStores', 'LegacyPins'):
        w.empty_dict(var)
    w.assign('LegacyOK', '1')
    loop, name = w.each(w.keys(legacy))
    bundle = text(get(legacy, name))
    valid_bundle = w.if_match(bundle, BUNDLE)
    valid_name = w.if_match(name, NAME)
    identifier = w.hash(bundle)
    already = exists_key(v('LegacyNames'), identifier)
    # Ambiguous aliases are rejected together, never silently discarded.
    w.assign('LegacyOK', '0')
    w.otherwise(already)
    for target, value in [('LegacyNames', name), ('LegacyBundles', bundle), ('LegacyStores', ''), ('LegacyPins', '0')]:
        w.set(target, put(v(target), identifier, value))
    w.end_if(already)
    w.otherwise(valid_name)
    w.assign('LegacyOK', '0')
    w.end_if(valid_name)
    w.otherwise(valid_bundle)
    w.assign('LegacyOK', '0')
    w.end_if(valid_bundle)
    w.end_loop(loop)
    okay = w.if_eq(v('LegacyOK'), '1')
    confirmed = menu([('✅', 'import', 'confirm'), ('↩️', 'back', 'back')], L('replaceConfirm'))
    yes = w.if_eq(confirmed, 'confirm')
    save(v('ImportText'), 'legacy-import-original.json')
    for target, source in [('Names', 'LegacyNames'), ('Bundles', 'LegacyBundles'), ('Stores', 'LegacyStores'), ('Pins', 'LegacyPins')]:
        w.set(target, v(source))
    request_save()
    w.otherwise(yes)
    w.set('Route', v('ImportReturn'))
    w.end_if(yes)
    w.otherwise(okay)
    w.alert(L('invalidData'), title=TITLE)
    w.set('Route', v('ImportReturn'))
    w.end_if(okay)
    w.otherwise(configured)
    w.assign('PendingImport', '1')
    w.assign('Route', 'configure')
    w.end_if(configured)
    w.otherwise(flat)
    w.alert(L('invalidData'), title=TITLE)
    w.set('Route', v('ImportReturn'))
    w.end_if(flat)
    w.end_if(modern)
    w.end_if(importing)

    saving = w.if_eq(v('PassRoute'), 'save')
    persist()
    show_message = w.if_match(v('SaveMessage'), r'\A(?:saved|removed|added)\z')
    a('notification', {'WFNotificationActionTitle': '',
        'WFNotificationActionBody': token(get(v('Strings'), v('SaveMessage'))),
        'WFNotificationActionSound': False})
    w.end_if(show_message)
    w.set('Route', v('AfterSave'))
    w.end_if(saving)

    info = w.if_eq(v('PassRoute'), 'info')
    w.alert(text('AppList Pro ', get(v('Config'), 'version'), '\n\n', L('infoBody')), title=TITLE)
    w.assign('Route', 'manage')
    w.end_if(info)
    cancel = w.if_eq(v('PassRoute'), 'cancel')
    a('exit')
    w.end_if(cancel)
    w.end_loop(interactions)
    a('exit')
    boot['values'] = w.constants
    w.actions[top_index]['WFWorkflowActionParameters']['WFItems'] = dictionary_value(boot)
    workflow = w.header()
    workflow['WFWorkflowName'] = 'AppList Pro beta4'
    workflow['WFWorkflowInputContentItemClasses'] = ['WFURLContentItem']
    workflow['WFWorkflowIcon'] = {'WFWorkflowIconStartColor': 431817727, 'WFWorkflowIconGlyphNumber': 59700}
    return workflow


def main():
    workflow = build()
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    binary = plistlib.dumps(workflow, fmt=plistlib.FMT_BINARY, sort_keys=False)
    (out / 'AppList-Pro.unsigned.bplist').write_bytes(binary)
    (out / 'AppList-Pro.unsigned.shortcut').write_bytes(plistlib.dumps(workflow, sort_keys=False))
    report = {'version': VERSION, 'actions': len(workflow['WFWorkflowActions']),
              'binaryBytes': len(binary), 'unsignedSHA256': hashlib.sha256(binary).hexdigest(),
              'nativeDeviceVerified': False}
    (ROOT / 'qa/build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
