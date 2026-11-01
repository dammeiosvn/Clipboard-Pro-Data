from pathlib import Path
import base64
import hashlib
import itertools
import json
import plistlib
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from build import build, FORMAT
from catalog import BASE_URL, LANGUAGES, package
from interpreter import File, run

WORKFLOW = build()
STRINGS = json.loads((ROOT / 'config/strings.json').read_text())
NETWORK = {BASE_URL + code + '.txt': json.dumps(package(strings)) for code, strings in STRINGS.items()}


def uid(bundle):
    return hashlib.sha256(bundle.encode()).hexdigest()


def envelope(state):
    raw = json.dumps(state, ensure_ascii=False, separators=(',', ':'))
    payload = base64.b64encode(raw.encode()).decode()
    return {'format': FORMAT, 'payload': payload, 'sha256': hashlib.sha256(payload.encode()).hexdigest()}


def state(records=(), lang='vi'):
    data = {'product': 'applist-pro', 'schema': '2', 'language': lang,
            'languagePayload': package(STRINGS[lang])['payload'],
            'names': {}, 'bundles': {}, 'stores': {}, 'pins': {}}
    for name, bundle, pin in records:
        key = uid(bundle)
        data['names'][key] = name
        data['bundles'][key] = bundle
        data['stores'][key] = 'https://apps.apple.com/vn/app/example/id123'
        data['pins'][key] = pin
    return data


def file_of(data):
    return File('active.json', json.dumps(envelope(data)))


def disk_of(data):
    return {'AppListPro/active.json': file_of(data)}


def read_state(result):
    env = json.loads(result['disk']['AppListPro/active.json'].body)
    return json.loads(base64.b64decode(env['payload']))


RECORDS = [('Messenger', 'com.facebook.Messenger', '0'),
           ('Messenger Kids', 'com.facebook.MessengerKids', '0'),
           ('Safari', 'com.apple.mobilesafari', '1')]
APP = {'name': 'Google Maps - Transit & Food', 'bundle': 'com.google.Maps',
       'url': 'https://apps.apple.com/vn/app/google-maps/id585027354'}


class NativeFlowTests(unittest.TestCase):
    def test_first_setup_fetches_one_language_and_returns_to_app_list(self):
        r = run(WORKFLOW, menus=['vi', 'manage', 'main'], network=NETWORK, rewrite_json=True)
        self.assertEqual(r['requests'], [BASE_URL + 'vi.txt'])
        self.assertEqual(read_state(r)['language'], 'vi')
        self.assertIn('➕ Thêm ứng dụng', r['menus'][1]['options'])
        self.assertEqual(r['menus'][1]['options'][-1], '⚙️ Quản lý')
        self.assertNotIn('vi', r['menus'][0]['options'])

    def test_direct_launch_is_first_menu_without_network_or_writes(self):
        r = run(WORKFLOW, menus=[uid('com.facebook.Messenger')], disk=disk_of(state(RECORDS)), rewrite_json=True)
        self.assertEqual(r['opened'], ['com.facebook.Messenger'])
        self.assertEqual(r['requests'], [])
        self.assertEqual(r['writes'], [])
        self.assertEqual(len(r['menus']), 1)
        self.assertEqual(r['menus'][0]['options'], ['⭐ Safari', 'Messenger', 'Messenger Kids', '⚙️ Quản lý'])

    def test_delete_exact_id_preserves_substring_name_and_can_undo(self):
        r = run(WORKFLOW, menus=['manage', 'pickDelete', uid('com.facebook.Messenger'), 'confirm'], disk=disk_of(state(RECORDS)))
        current = read_state(r)
        self.assertNotIn(uid('com.facebook.Messenger'), current['names'])
        self.assertIn(uid('com.facebook.MessengerKids'), current['names'])
        restored = run(WORKFLOW, menus=['manage', 'backups', 'restore', 'confirm'], disk=r['disk'])
        self.assertEqual(read_state(restored)['names'], state(RECORDS)['names'])

    def test_cancel_delete_does_not_write(self):
        r = run(WORKFLOW, menus=['manage', 'pickDelete', uid('com.facebook.Messenger'), 'back'], disk=disk_of(state(RECORDS)))
        self.assertEqual(r['writes'], [])
        self.assertEqual(read_state(r)['names'], state(RECORDS)['names'])

    def test_add_keeps_full_name_and_deduplicates_bundle(self):
        r = run(WORKFLOW, menus=['manage', 'add', 'search', 0], answers=['maps'], apps=[APP], disk=disk_of(state(RECORDS)), rewrite_json=True)
        saved = read_state(r)
        self.assertEqual(saved['names'][uid(APP['bundle'])], APP['name'])
        again = run(WORKFLOW, menus=['manage', 'add', 'search', 0], answers=['maps'], apps=[{**APP, 'name': 'Different label'}], disk=r['disk'])
        self.assertEqual(again['writes'], [])
        self.assertIn(STRINGS['vi']['exists'], again['alerts'])

    def test_duplicate_display_name_requires_rename(self):
        app = {**APP, 'name': 'Messenger'}
        r = run(WORKFLOW, menus=['manage', 'add', 'search', 0], answers=['maps', 'Messenger Maps'], apps=[app], disk=disk_of(state(RECORDS)))
        self.assertEqual(read_state(r)['names'][uid(APP['bundle'])], 'Messenger Maps')

    def test_quote_backslash_emoji_and_dollar_are_serialized_safely(self):
        name = 'Bản "A" \\ thử $5 😎'
        r = run(WORKFLOW, menus=['manage', 'pickEdit', uid('com.facebook.Messenger'), 'rename'], answers=[name], disk=disk_of(state(RECORDS)), rewrite_json=True)
        self.assertEqual(read_state(r)['names'][uid('com.facebook.Messenger')], name)
        reopened = run(WORKFLOW, menus=[uid('com.facebook.Messenger')], disk=r['disk'], rewrite_json=True)
        self.assertEqual(reopened['opened'], ['com.facebook.Messenger'])

    def test_duplicate_or_control_name_does_not_mutate_disk(self):
        for name in ['Safari', '\n', '⭐ App', '⚙️ Quản lý', 'a'*91]:
            with self.subTest(name=name):
                r = run(WORKFLOW, menus=['manage', 'pickEdit', uid('com.facebook.Messenger'), 'rename'], answers=[name, None], disk=disk_of(state(RECORDS)))
                self.assertEqual(r['writes'], [])
                self.assertEqual(read_state(r)['names'], state(RECORDS)['names'])

    def test_pin_reorders_outer_list(self):
        r = run(WORKFLOW, menus=['manage', 'pickEdit', uid('com.facebook.Messenger'), 'pin', uid('com.facebook.Messenger')], disk=disk_of(state(RECORDS)))
        self.assertEqual(r['menus'][-1]['options'][0], '⭐ Messenger')
        self.assertEqual(r['opened'], ['com.facebook.Messenger'])

    def test_no_results_and_cancelled_input_leave_data_unchanged(self):
        for answers in [['unknown'], [None], ['   ']]:
            with self.subTest(answers=answers):
                r = run(WORKFLOW, menus=['manage', 'add', 'search'], answers=answers, disk=disk_of(state(RECORDS)))
                self.assertEqual(r['writes'], [])

    def test_shared_app_store_link_adds_without_launching_other_menu(self):
        link = APP['url']
        network = {'https://itunes.apple.com/lookup?id=585027354&country=vn': json.dumps({'results': [
            {'bundleId': APP['bundle'], 'trackName': APP['name'], 'trackViewUrl': APP['url']}], 'resultCount': 1})}
        r = run(WORKFLOW, incoming=link, network=network, disk=disk_of(state(RECORDS)))
        self.assertIn(uid(APP['bundle']), read_state(r)['names'])
        self.assertEqual(r['opened'], [])

    def test_unrelated_shared_link_does_not_become_network_request(self):
        r = run(WORKFLOW, incoming='https://example.com/private', menus=[uid('com.facebook.Messenger')], disk=disk_of(state(RECORDS)))
        self.assertEqual(r['requests'], [])
        self.assertEqual(r['opened'], ['com.facebook.Messenger'])

    def test_app_store_route_only_opens_store(self):
        r = run(WORKFLOW, menus=['manage', 'store', 0], answers=['maps'], apps=[APP], disk=disk_of(state(RECORDS)))
        self.assertEqual(r['opened'], [APP['url']])
        self.assertEqual(r['writes'], [])

    def test_native_open_error_does_not_claim_install_or_autorecovery(self):
        r = run(WORKFLOW, menus=[uid('com.facebook.Messenger')], disk=disk_of(state(RECORDS)), unavailable_apps=['com.facebook.Messenger'])
        self.assertEqual(r['status'], 'app-error')
        self.assertEqual(r['writes'], [])
        self.assertEqual(r['requests'], [])

    def test_bad_active_recovers_from_previous_and_main_stays_outermost(self):
        for bad in ['{"format":"truncated', '{"format":"applist-active-v2"}', json.dumps({**envelope(state(RECORDS)), 'sha256': '0'*64})]:
            disk = {'AppListPro/active.json': File('active.json', bad), 'AppListPro/active.previous.json': file_of(state(RECORDS))}
            r = run(WORKFLOW, menus=[uid('com.facebook.Messenger')], disk=disk)
            self.assertEqual(r['opened'], ['com.facebook.Messenger'])
            self.assertEqual(r['alerts'], [STRINGS['vi']['recovered']])
            self.assertEqual(r['writes'], [])

    def test_all_six_outer_key_orders_are_accepted(self):
        env = envelope(state(RECORDS))
        for order in itertools.permutations(env):
            with self.subTest(order=order):
                file = File('active.json', json.dumps({k: env[k] for k in order}, indent=2))
                r = run(WORKFLOW, menus=[uid('com.facebook.Messenger')], disk={'AppListPro/active.json': file})
                self.assertEqual(r['opened'], ['com.facebook.Messenger'])

    def test_wrong_state_schema_rejected_before_open(self):
        wrong = state(RECORDS)
        wrong['schema'] = '999'
        r = run(WORKFLOW, menus=['cancel'], disk=disk_of(wrong))
        self.assertEqual(r['opened'], [])
        self.assertEqual(r['writes'], [])

    def test_import_backup_validates_every_record_before_replace(self):
        bad = state(RECORDS)
        bad['bundles'][uid('com.facebook.Messenger')] = 'com.bad.changed'
        r = run(WORKFLOW, menus=['manage', 'backups', 'import'], files=[file_of(bad)], disk=disk_of(state(RECORDS)))
        self.assertEqual(r['writes'], [])
        self.assertEqual(read_state(r), state(RECORDS))

    def test_legacy_import_preserves_original_and_migrates(self):
        original = File('AppList_Pro.json', json.dumps({'Google Maps': APP['bundle'], 'Safari': 'com.apple.mobilesafari'}))
        r = run(WORKFLOW, menus=['manage', 'backups', 'import', 'confirm'], files=[original], disk=disk_of(state(RECORDS)))
        self.assertEqual(set(read_state(r)['names'].values()), {'Google Maps', 'Safari'})
        self.assertEqual(r['disk']['AppListPro/legacy-import-original.json'].body, original.body)
        self.assertEqual(json.loads(original.body)['Google Maps'], APP['bundle'])

    def test_ambiguous_legacy_aliases_are_not_silently_discarded(self):
        original = File('AppList_Pro.json', json.dumps({'A': APP['bundle'], 'B': APP['bundle']}))
        r = run(WORKFLOW, menus=['manage', 'backups', 'import'], files=[original], disk=disk_of(state(RECORDS)))
        self.assertEqual(r['writes'], [])

    def test_bad_staged_write_never_replaces_active(self):
        r = run(WORKFLOW, menus=['manage', 'pickEdit', uid('com.facebook.Messenger'), 'pin'], disk=disk_of(state(RECORDS)), corrupt_save='AppListPro/active.pending.json')
        self.assertEqual(read_state(r), state(RECORDS))
        self.assertNotIn('AppListPro/active.json', r['writes'])
        self.assertIn(STRINGS['vi']['saveFailed'], r['alerts'])

    def test_io_failure_keeps_current_or_verified_previous_file(self):
        for path in ['AppListPro/active.pending.json', 'AppListPro/active.previous.json', 'AppListPro/active.json']:
            with self.subTest(path=path):
                r = run(WORKFLOW, menus=['manage', 'pickEdit', uid('com.facebook.Messenger'), 'pin'], disk=disk_of(state(RECORDS)), fail_save=path)
                self.assertEqual(r['status'], 'io-error')
                self.assertEqual(read_state(r), state(RECORDS))

    def test_changed_local_revision_is_not_overwritten(self):
        def update_other_session(path, result):
            if path == 'AppListPro/active.json' and result['reads'].count(path) == 2:
                result['disk'][path] = file_of(state(RECORDS + [('Other', 'com.other.App', '0')]))
        r = run(WORKFLOW, menus=['manage', 'pickEdit', uid('com.facebook.Messenger'), 'pin'], disk=disk_of(state(RECORDS)), on_read=update_other_session)
        self.assertIn(uid('com.other.App'), read_state(r)['names'])
        self.assertEqual(r['writes'], [])
        self.assertIn(STRINGS['vi']['changedElsewhere'], r['alerts'])

    def test_network_failure_switching_language_preserves_current(self):
        r = run(WORKFLOW, menus=['manage', 'language', 'ja'], disk=disk_of(state(RECORDS)), network={})
        self.assertEqual(r['status'], 'network-error')
        self.assertEqual(r['writes'], [])
        self.assertEqual(read_state(r)['language'], 'vi')

    def test_all_twenty_languages_have_info_and_use_same_launch_flow(self):
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                r = run(WORKFLOW, menus=['manage', 'info'], disk=disk_of(state(RECORDS, lang)), rewrite_json=True)
                self.assertIn(STRINGS[lang]['infoBody'], r['alerts'])
                self.assertEqual(r['requests'], [])
                self.assertEqual(r['writes'], [])

    def test_export_is_private_file_not_upload(self):
        r = run(WORKFLOW, menus=['manage', 'backups', 'export'], disk=disk_of(state(RECORDS)))
        self.assertEqual(len(r['exports']), 1)
        self.assertEqual(r['requests'], [])
        self.assertEqual(r['writes'], [])


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    report = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'passed': result.wasSuccessful(), 'nativeDeviceVerified': False}
    (ROOT / 'qa/test-results.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
