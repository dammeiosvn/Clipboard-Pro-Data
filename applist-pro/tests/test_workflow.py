from pathlib import Path
import hashlib
import json
import plistlib
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from build import build, ACTIVE, PREVIOUS, PENDING, LABELS
from catalog import BASE_URL, DATA_VERSION, LANGUAGES
from interpreter import File, run

WORKFLOW = build()
STRINGS = json.loads((ROOT / 'config/strings.json').read_text())
NETWORK = {BASE_URL + code + '.json': json.dumps(strings) for code, strings in STRINGS.items()}


def uid(bundle):
    return hashlib.sha256(bundle.encode()).hexdigest()


def native_state(data):
    fields = {key: data[key] for key in ('product', 'schema', 'language')}
    fields['revision'] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    for key in ('names', 'bundles', 'stores', 'pins'):
        fields[key + 'JSON'] = json.dumps(data[key], ensure_ascii=False)
    for key in set(data) - {'product', 'schema', 'language', 'names', 'bundles', 'stores', 'pins'}:
        fields[key] = data[key]
    return fields


def state(records=(), lang='vi'):
    data = {'product': 'applist-pro', 'schema': '4', 'language': lang,
            'names': {}, 'bundles': {}, 'stores': {}, 'pins': {}}
    for name, bundle, pin in records:
        key = uid(bundle)
        data['names'][key] = name
        data['bundles'][key] = bundle
        data['stores'][key] = 'https://apps.apple.com/vn/app/example/id123'
        data['pins'][key] = pin
    return data


def file_of(data):
    return File(ACTIVE, json.dumps(native_state(data)))


def cache_of(lang='vi'):
    return File(LABELS, json.dumps({**STRINGS[lang], '_locale': lang, '_dataVersion': DATA_VERSION}))


def disk_of(data):
    return {'AppListPro/' + ACTIVE: file_of(data), 'AppListPro/' + LABELS: cache_of(data['language'])}


def read_state(result):
    raw = json.loads(result['disk']['AppListPro/' + ACTIVE].body)
    data = {key: raw[key] for key in ('product', 'schema', 'language')}
    for key in ('names', 'bundles', 'stores', 'pins'):
        data[key] = json.loads(raw[key + 'JSON'])
    return data


RECORDS = [('Messenger', 'com.facebook.Messenger', '0'),
           ('Messenger Kids', 'com.facebook.MessengerKids', '0'),
           ('Safari', 'com.apple.mobilesafari', '1')]
APP = {'name': 'Google Maps - Transit & Food', 'bundle': 'com.google.Maps',
       'url': 'https://apps.apple.com/vn/app/google-maps/id585027354'}


class NativeFlowTests(unittest.TestCase):
    def test_first_setup_fetches_one_language_and_returns_to_app_list(self):
        r = run(WORKFLOW, menus=['vi', 'manage', 'main'], network=NETWORK, rewrite_json=True)
        self.assertEqual(r['requests'], [BASE_URL + 'vi.json'])
        self.assertEqual(read_state(r)['language'], 'vi')
        self.assertIn('➕ Thêm ứng dụng', r['menus'][1]['options'])
        self.assertEqual(r['menus'][1]['options'][-1], '⚙️ Quản lý')
        self.assertNotIn('vi', r['menus'][0]['options'])
        self.assertEqual(r['alerts'], [])
        self.assertEqual(r['menus'][0]['options'][0], 'Tiếng Việt')

    def test_new_list_from_recovery_does_not_report_false_concurrent_change(self):
        broken = File(ACTIVE, '{"format":"truncated')
        r = run(WORKFLOW, menus=['configure', 'vi'], network=NETWORK,
                disk={'AppListPro/' + ACTIVE: broken}, rewrite_json=True)
        self.assertEqual(read_state(r)['names'], {})
        self.assertNotIn(STRINGS['vi']['changedElsewhere'], r['alerts'])
        self.assertEqual(r['disk']['AppListPro/unreadable-before-reset.v4.json'].body, broken.body)

    def test_legacy_import_from_recovery_keeps_selection_through_language_setup(self):
        broken = File(ACTIVE, '{"format":"truncated')
        legacy = File('AppList_Pro.json', '{"Safari":"com.apple.mobilesafari"}')
        r = run(WORKFLOW, menus=['import', 'vi', 'confirm'], files=[legacy], network=NETWORK,
                disk={'AppListPro/' + ACTIVE: broken}, rewrite_json=True)
        self.assertEqual(set(read_state(r)['names'].values()), {'Safari'})
        self.assertEqual(r['filePickers'], 1)
        self.assertEqual(r['ignoredLegacyPickers'], 0)
        self.assertEqual(r['disk']['AppListPro/unreadable-before-reset.v4.json'].body, broken.body)
        self.assertEqual(json.loads(r['disk']['AppListPro/legacy-import-original.json'].body), json.loads(legacy.body))

    def test_pending_legacy_import_cancelled_at_confirmation_never_saves_empty_list(self):
        broken = File(ACTIVE, '{"format":"truncated')
        legacy = File('AppList_Pro.json', '{"Safari":"com.apple.mobilesafari"}')
        r = run(WORKFLOW, menus=['import', 'vi', 'back', 'cancel'], files=[legacy], network=NETWORK,
                disk={'AppListPro/' + ACTIVE: broken})
        self.assertFalse(any(path in r['writes'] for path in ['AppListPro/' + name for name in (ACTIVE, PREVIOUS, PENDING)]))
        self.assertEqual(r['disk']['AppListPro/' + ACTIVE], broken)

    def test_cancel_native_file_picker_keeps_data_and_does_not_show_invalid_json(self):
        r = run(WORKFLOW, menus=['manage', 'backups', 'import'], files=[None], disk=disk_of(state(RECORDS)))
        self.assertEqual(r['status'], 'cancelled')
        self.assertEqual(r['filePickers'], 1)
        self.assertEqual(r['writes'], [])
        self.assertEqual(r['alerts'], [])

    def test_import_accepts_utf8_bom_from_files(self):
        legacy = File('AppList_Pro.json', '\ufeff{"Safari":"com.apple.mobilesafari"}')
        r = run(WORKFLOW, menus=['manage', 'backups', 'import', 'confirm'], files=[legacy], disk=disk_of(state(RECORDS)))
        self.assertEqual(set(read_state(r)['names'].values()), {'Safari'})
        self.assertEqual(r['filePickers'], 1)

    def test_modern_backup_from_recovery_does_not_require_network_or_language_setup(self):
        backup = file_of(state(RECORDS))
        broken = File(ACTIVE, '{"format":"truncated')
        r = run(WORKFLOW, menus=['import', 'confirm'], files=[backup], disk={'AppListPro/' + ACTIVE: broken})
        self.assertEqual(read_state(r)['names'], state(RECORDS)['names'])
        self.assertEqual(r['requests'], [])
        self.assertEqual(r['filePickers'], 1)

    def test_direct_launch_is_first_menu_without_network_or_writes(self):
        r = run(WORKFLOW, menus=[uid('com.facebook.Messenger')], disk=disk_of(state(RECORDS)), rewrite_json=True)
        self.assertEqual(r['opened'], ['com.facebook.Messenger'])
        self.assertEqual(r['requests'], [])
        self.assertEqual(r['writes'], [])
        self.assertEqual(len(r['menus']), 1)
        self.assertEqual(r['menus'][0]['options'], ['⭐ Safari', 'Messenger', 'Messenger Kids', '⚙️ Quản lý'])

    def test_setup_empty_maps_can_be_read_again_after_session_ends(self):
        first = run(WORKFLOW, menus=['vi'], network=NETWORK, native_empty_dict_text=True,
                    native_state_reorder=True, rewrite_json=True)
        self.assertEqual(first['alerts'], [])
        self.assertEqual(read_state(first)['names'], {})
        again = run(WORKFLOW, menus=['manage', 'main'], disk=first['disk'],
                    native_empty_dict_text=True, native_state_reorder=True, rewrite_json=True)
        self.assertEqual(again['alerts'], [])
        self.assertEqual(again['requests'], [])
        self.assertEqual(again['writes'], [])
        self.assertEqual(again['menus'][0]['options'], ['➕ Thêm ứng dụng', '⚙️ Quản lý'])

    def test_new_app_is_saved_and_opens_on_the_next_run(self):
        first = run(WORKFLOW, menus=['manage', 'add', 'search', 0], answers=['Candy'], apps=[APP],
                    disk=disk_of(state()), native_empty_dict_text=True, native_state_reorder=True, rewrite_json=True)
        self.assertEqual(first['alerts'], [])
        again = run(WORKFLOW, menus=[uid(APP['bundle'])], disk=first['disk'],
                    native_empty_dict_text=True, native_state_reorder=True, rewrite_json=True)
        self.assertEqual(again['opened'], [APP['bundle']])
        self.assertEqual(again['requests'], [])
        self.assertEqual(again['writes'], [])

    def test_legacy_json_is_saved_and_opens_on_the_next_run(self):
        legacy = File('AppList_Pro.json', '{"Safari":"com.apple.mobilesafari"}')
        first = run(WORKFLOW, menus=['manage', 'backups', 'import', 'confirm'], files=[legacy],
                    disk=disk_of(state()), native_empty_dict_text=True, native_state_reorder=True, rewrite_json=True)
        self.assertEqual(first['alerts'], [])
        again = run(WORKFLOW, menus=[uid('com.apple.mobilesafari')], disk=first['disk'],
                    native_empty_dict_text=True, native_state_reorder=True, rewrite_json=True)
        self.assertEqual(again['opened'], ['com.apple.mobilesafari'])
        self.assertEqual(again['alerts'], [])

    def test_inner_property_order_is_not_a_cache_requirement(self):
        source = state(RECORDS)
        orders = [sorted(source), list(reversed(source))]
        for offset in range(len(source)):
            keys = list(source)
            orders.append(keys[offset:] + keys[:offset])
        for order in orders:
            with self.subTest(order=order):
                reordered = {key: source[key] for key in order}
                r = run(WORKFLOW, menus=[uid('com.facebook.Messenger')], disk=disk_of(reordered))
                self.assertEqual(r['opened'], ['com.facebook.Messenger'])
                self.assertEqual(r['alerts'], [])

    def test_native_numeric_pin_flags_are_supported(self):
        source = state(RECORDS)
        source['pins'] = {key: int(value) for key, value in source['pins'].items()}
        r = run(WORKFLOW, menus=[uid('com.apple.mobilesafari')], disk=disk_of(source))
        self.assertEqual(r['opened'], ['com.apple.mobilesafari'])
        self.assertEqual(r['menus'][0]['options'][0], '⭐ Safari')

    def test_extra_state_properties_are_rejected_without_overwriting(self):
        source = state(RECORDS)
        source['unexpected'] = 'field'
        r = run(WORKFLOW, menus=['cancel'], disk=disk_of(source))
        self.assertEqual(r['opened'], [])
        self.assertEqual(r['writes'], [])

    def test_deleting_last_app_keeps_a_reloadable_empty_list(self):
        source = state([RECORDS[0]])
        first = run(WORKFLOW, menus=['manage', 'pickDelete', uid(RECORDS[0][1]), 'confirm'],
                    disk=disk_of(source), native_empty_dict_text=True, native_state_reorder=True)
        again = run(WORKFLOW, menus=['manage'], disk=first['disk'],
                    native_empty_dict_text=True, native_state_reorder=True)
        self.assertEqual(read_state(again)['names'], {})
        self.assertEqual(again['alerts'], [])

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
        for bad in ['{"format":"truncated', '{"format":"applist-active-v2"}', json.dumps({**native_state(state(RECORDS)), 'revision': 'invalid'})]:
            disk = {'AppListPro/' + ACTIVE: File(ACTIVE, bad), 'AppListPro/' + PREVIOUS: file_of(state(RECORDS)), 'AppListPro/' + LABELS: cache_of()}
            r = run(WORKFLOW, menus=[uid('com.facebook.Messenger')], disk=disk)
            self.assertEqual(r['opened'], ['com.facebook.Messenger'])
            self.assertEqual(r['alerts'], [STRINGS['vi']['recovered']])
            self.assertEqual(r['writes'], [])

    def test_native_file_key_order_is_not_significant(self):
        env = native_state(state(RECORDS))
        for order in [list(env), list(reversed(env)), sorted(env)]:
            with self.subTest(order=order):
                file = File(ACTIVE, json.dumps({k: env[k] for k in order}, indent=2))
                r = run(WORKFLOW, menus=[uid('com.facebook.Messenger')], disk={'AppListPro/' + ACTIVE: file})
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
        r = run(WORKFLOW, menus=['manage', 'pickEdit', uid('com.facebook.Messenger'), 'pin'], disk=disk_of(state(RECORDS)), corrupt_save='AppListPro/' + PENDING)
        self.assertEqual(read_state(r), state(RECORDS))
        self.assertNotIn('AppListPro/' + ACTIVE, r['writes'])
        self.assertTrue(any(STRINGS['vi']['saveFailed'] in alert for alert in r['alerts']))

    def test_io_failure_keeps_current_or_verified_previous_file(self):
        for path in ['AppListPro/' + PENDING, 'AppListPro/' + PREVIOUS, 'AppListPro/' + ACTIVE]:
            with self.subTest(path=path):
                r = run(WORKFLOW, menus=['manage', 'pickEdit', uid('com.facebook.Messenger'), 'pin'], disk=disk_of(state(RECORDS)), fail_save=path)
                self.assertEqual(r['status'], 'io-error')
                self.assertEqual(read_state(r), state(RECORDS))

    def test_changed_local_revision_is_not_overwritten(self):
        def update_other_session(path, result):
            if path == 'AppListPro/' + ACTIVE and result['reads'].count(path) == 2:
                result['disk'][path] = file_of(state(RECORDS + [('Other', 'com.other.App', '0')]))
        r = run(WORKFLOW, menus=['manage', 'pickEdit', uid('com.facebook.Messenger'), 'pin'], disk=disk_of(state(RECORDS)), on_read=update_other_session)
        self.assertIn(uid('com.other.App'), read_state(r)['names'])
        self.assertEqual(r['writes'], [])
        self.assertTrue(any(STRINGS['vi']['changedElsewhere'] in alert for alert in r['alerts']))

    def test_network_failure_switching_language_preserves_current(self):
        r = run(WORKFLOW, menus=['manage', 'language', 'ja'], disk=disk_of(state(RECORDS)), network={})
        self.assertEqual(r['status'], 'network-error')
        self.assertEqual(r['writes'], [])
        self.assertEqual(read_state(r)['language'], 'vi')

    def test_all_twenty_languages_have_info_and_use_same_launch_flow(self):
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                r = run(WORKFLOW, menus=['manage', 'info'], disk=disk_of(state(RECORDS, lang)), rewrite_json=True)
                self.assertTrue(any(STRINGS[lang]['infoBody'] in alert for alert in r['alerts']))
                self.assertEqual(r['requests'], [])
                self.assertEqual(r['writes'], [])

    def test_export_is_private_file_not_upload(self):
        r = run(WORKFLOW, menus=['manage', 'backups', 'export'], disk=disk_of(state(RECORDS)))
        self.assertEqual(len(r['exports']), 1)
        self.assertEqual(r['requests'], [])
        self.assertEqual(r['writes'], [])

    def test_missing_damaged_or_mismatched_language_cache_cannot_block_launch(self):
        for cache in [None, File(LABELS, '{truncated'), cache_of('ja')]:
            with self.subTest(cache=cache):
                disk = disk_of(state(RECORDS))
                disk.pop('AppListPro/' + LABELS)
                if cache:
                    disk['AppListPro/' + LABELS] = cache
                r = run(WORKFLOW, menus=[uid(RECORDS[0][1])], disk=disk)
                self.assertEqual(r['opened'], [RECORDS[0][1]])
                self.assertEqual(r['alerts'], [])
                self.assertEqual(r['requests'], [])
                self.assertEqual(r['writes'], [])

    def test_previous_language_cache_is_used_before_english_fallback(self):
        disk = disk_of(state(RECORDS))
        disk['AppListPro/' + LABELS] = File(LABELS, '{}')
        disk['AppListPro/labels.previous.v4.json'] = cache_of()
        r = run(WORKFLOW, menus=[uid(RECORDS[0][1])], disk=disk)
        self.assertEqual(r['menus'][0]['options'][-1], '⚙️ Quản lý')
        self.assertEqual(r['requests'], [])

    def test_old_beta_files_are_preserved_during_fresh_setup(self):
        old = File('active.json', '{"format":"applist-active-v2","payload":"old"}')
        r = run(WORKFLOW, menus=['vi'], network=NETWORK, disk={'AppListPro/active.json': old})
        self.assertEqual(r['disk']['AppListPro/active.json'], old)
        self.assertEqual(read_state(r)['names'], {})
        self.assertEqual(r['alerts'], [])

    def test_staged_valid_json_with_wrong_value_is_rejected_before_replace(self):
        def corrupt(path, file):
            if path == 'AppListPro/' + PENDING:
                data = json.loads(file.body)
                names = json.loads(data['namesJSON'])
                names[uid(RECORDS[0][1])] = 'Unexpected change'
                data['namesJSON'] = json.dumps(names)
                return File(file.name, json.dumps(data))
            return file
        r = run(WORKFLOW, menus=['manage', 'pickEdit', uid(RECORDS[0][1]), 'pin'],
                disk=disk_of(state(RECORDS)), corrupt_save=corrupt)
        self.assertNotIn('AppListPro/' + ACTIVE, r['writes'])
        self.assertNotIn('AppListPro/' + PREVIOUS, r['writes'])
        self.assertEqual(read_state(r), state(RECORDS))
        self.assertTrue(any('AP4 / ' + PENDING in alert for alert in r['alerts']))

    def test_failed_final_write_can_recover_the_verified_previous_list(self):
        first = run(WORKFLOW, menus=['manage', 'pickEdit', uid(RECORDS[0][1]), 'pin'],
                    disk=disk_of(state(RECORDS)), corrupt_save='AppListPro/' + ACTIVE)
        self.assertTrue(any('AP4 / ' + ACTIVE in alert for alert in first['alerts']))
        again = run(WORKFLOW, menus=[uid(RECORDS[0][1])], disk=first['disk'])
        self.assertEqual(again['opened'], [RECORDS[0][1]])
        self.assertIn(STRINGS['vi']['recovered'], again['alerts'])

    def test_concurrent_revision_after_staging_is_not_overwritten(self):
        def update_other_session(path, result):
            if path == 'AppListPro/' + ACTIVE and result['reads'].count(path) == 3:
                result['disk'][path] = file_of(state(RECORDS + [('Other', 'com.other.App', '0')]))
        r = run(WORKFLOW, menus=['manage', 'pickEdit', uid(RECORDS[0][1]), 'pin'],
                disk=disk_of(state(RECORDS)), on_read=update_other_session)
        self.assertNotIn('AppListPro/' + ACTIVE, r['writes'])
        self.assertIn(uid('com.other.App'), read_state(r)['names'])
        self.assertIn(STRINGS['vi']['changedElsewhere'], r['alerts'])

    def test_exported_native_backup_can_be_imported_offline_after_file_reformatting(self):
        first = run(WORKFLOW, menus=['manage', 'backups', 'export'], disk=disk_of(state(RECORDS)))
        backup = json.loads(first['exports'][0].body)
        file = File('backup.json', json.dumps(backup, ensure_ascii=True, indent=4).replace('/', '\\/'))
        second = run(WORKFLOW, menus=['manage', 'backups', 'import', 'confirm'], files=[file],
                     disk=disk_of(state()))
        self.assertEqual(read_state(second), state(RECORDS))
        self.assertEqual(second['requests'], [])

    def test_switching_language_is_cached_for_the_next_launch(self):
        first = run(WORKFLOW, menus=['manage', 'language', 'ja'], network=NETWORK, disk=disk_of(state(RECORDS)))
        self.assertEqual(first['requests'], [BASE_URL + 'ja.json'])
        self.assertEqual(read_state(first)['language'], 'ja')
        again = run(WORKFLOW, menus=['manage', 'info'], disk=first['disk'])
        self.assertTrue(any(STRINGS['ja']['infoBody'] in alert for alert in again['alerts']))
        self.assertEqual(again['requests'], [])

    def test_duplicate_state_fields_are_rejected_before_key_lookup(self):
        data = native_state(state(RECORDS))
        data.pop('revision')
        raw = json.dumps(data)[:-1] + ',"schema":"4"}'
        r = run(WORKFLOW, menus=['cancel'], disk={'AppListPro/' + ACTIVE: File(ACTIVE, raw)})
        self.assertEqual(r['opened'], [])
        self.assertEqual(r['writes'], [])
        self.assertTrue(r['alerts'])


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    report = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'passed': result.wasSuccessful(), 'nativeDeviceVerified': False}
    (ROOT / 'qa/test-results.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
