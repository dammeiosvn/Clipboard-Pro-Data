from pathlib import Path
import sys,json,hashlib,unittest,copy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from build import build,build_screen,BASE,VERSION,MAIN_NAME,SCREEN_NAME
from interpreter import run,File,Image,Page,PDF
WORKFLOW=build();SCREEN=build_screen()
STRINGS=json.loads((ROOT/'config/strings.json').read_text());LANGUAGES=json.loads((ROOT/'config/languages.json').read_text())
CATALOG=json.loads((ROOT/'resources/v1/catalog.json').read_text())
PACKS={c:json.loads((ROOT/('resources/v1/ui/'+c+'.json')).read_text()) for c in ('vi','en')}
def cfg(ui='vi',source='auto',target='vi'):
 return {'product':'quick-translation','schema':'1','ui':ui,'source':source,'target':target,'revision':'a'*64}
def file(name,data):return File(name,json.dumps(data,ensure_ascii=False))
def disk(settings=None):
 settings=settings or cfg();ui=settings['ui']
 return {'QuickTranslation/settings.json':file('settings.json',settings),'QuickTranslation/catalog.json':file('catalog.json',CATALOG),'QuickTranslation/ui.'+ui+'.json':file('ui.'+ui+'.json',PACKS[ui])}
def network(*locales,catalog=CATALOG):return {BASE+'catalog.json':catalog,**{BASE+'ui/'+code+'.json':PACKS[code] for code in locales}}
def sha(x):return hashlib.sha256(x.encode()).hexdigest()
def record(source='Hello',translation='Xin chào',target='vi',source_lang='auto'):
 sid=sha(source);rid=sha('|'.join([sid,source_lang,target,'apple-translate','1']))
 return {'product':'quick-translation-record','schema':'1','id':rid,'sourceHash':sid,'targetHash':sha(translation),'sourceText':source,'targetText':translation,'sourceLang':source_lang,'targetLang':target,'detectedSource':'English','engine':'apple-translate','engineRevision':'1','createdAt':'2026-11-01 23:00:00 +0700','inputKind':'text'}
def add_record(files,item):return {**files,'QuickTranslation/records/'+item['id']+'.json':file(item['id']+'.json',item)}

class StartupTests(unittest.TestCase):
 def test_first_setup_keeps_shared_text_and_only_downloads_selected_pack(self):
  r=run(WORKFLOW,incoming='Hello',network=network('vi'),menus=['vi','vi'],responses=['Xin chào'])
  self.assertEqual(r['translationCalls'],[{'text':'Hello','target':'vi_VN','source':'Detected language'}])
  self.assertEqual(r['requests'],[BASE+'catalog.json',BASE+'ui/vi.json'])
  self.assertTrue(any('Xin chào' in x for x in r['previews']));self.assertEqual(r['copied'],[])
 def test_direct_launch_has_nine_source_rows_without_clipboard_or_network(self):
  r=run(WORKFLOW,disk=disk())
  self.assertEqual(r['variables']['Route'],'main');self.assertEqual(len(r['variables']['Rows']),9)
  self.assertEqual(r['requests'],[]);self.assertEqual(r['writes'],[]);self.assertEqual(r['clipboardReads'],0)
 def test_ordinary_shared_text_uses_saved_target_and_no_setup(self):
  r=run(WORKFLOW,disk=disk(cfg(target='ja')),incoming='Hello',responses=['こんにちは'])
  self.assertEqual(r['translationCalls'][0]['target'],'ja_JP');self.assertEqual(r['writes'],[])
 def test_resources_json_reserialization_does_not_change_validation(self):
  r=run(WORKFLOW,network=network('en'),menus=['en','en'],rewrite_json=True,native_state_reorder=True,native_empty_dict_text=True)
  self.assertEqual(r['variables']['UI'],'en');self.assertIn('QuickTranslation/settings.json',r['disk'])
 def test_current_settings_recover_from_previous_without_network(self):
  d=disk();d['QuickTranslation/settings.previous.json']=d['QuickTranslation/settings.json'];d['QuickTranslation/settings.json']=File('settings.json','{bad')
  r=run(WORKFLOW,disk=d)
  self.assertIn(STRINGS['vi']['recovered'],r['previews']);self.assertEqual(r['requests'],[])
 def test_bad_settings_reconfigure_without_deleting_saved_records(self):
  item=record();d=add_record(disk(),item);d['QuickTranslation/settings.json']=File('settings.json','{bad')
  r=run(WORKFLOW,disk=d,menus=['vi','ja'])
  self.assertEqual(r['disk']['QuickTranslation/records/'+item['id']+'.json'],d['QuickTranslation/records/'+item['id']+'.json'])
  self.assertEqual(r['variables']['TargetLang'],'ja')

class InputTests(unittest.TestCase):
 def test_manual_and_explicit_clipboard_routes(self):
  for route,kwargs in [('manual',{'answers':['Hello']}),('clipboard',{'clipboard':'Hello'})]:
   with self.subTest(route=route):
    r=run(WORKFLOW,disk=disk(),menus=[route],responses=['Xin chào'],**kwargs)
    self.assertEqual(r['translationCalls'][0]['text'],'Hello');self.assertEqual(r['clipboardReads'],1 if route=='clipboard' else 0)
 def test_image_ocr_is_editable_before_translation(self):
  r=run(WORKFLOW,disk=disk(),incoming=Image('screen.png','Helo 123'),answers=['Hello 123'],responses=['Xin chào 123'])
  self.assertEqual(r['ocrCalls'],['screen.png']);self.assertEqual(r['translationCalls'][0]['text'],'Hello 123');self.assertEqual(r['writes'],[])
 def test_blank_ocr_can_be_entered_manually(self):
  r=run(WORKFLOW,disk=disk(),incoming=Image('blank.png',''),answers=['Manual fallback'],responses=['Dịch'])
  self.assertEqual(r['translationCalls'][0]['text'],'Manual fallback');self.assertIn(STRINGS['vi']['noImageText'],r['previews'])
 def test_cancel_ocr_review_never_translates_or_saves(self):
  r=run(WORKFLOW,disk=disk(),incoming=Image('screen.png','Hello'),answers=[None])
  self.assertEqual(r['status'],'cancelled');self.assertEqual(r['translationCalls'],[]);self.assertEqual(r['writes'],[])
 def test_photo_camera_and_file_image_sources(self):
  for route,kwargs in [('photos',{'photos':[Image('p.png','Hello')]}),('camera',{'camera':Image('c.png','Hello')}),('files',{'files':[Image('f.png','Hello','File')]})]:
   with self.subTest(route=route):
    r=run(WORKFLOW,disk=disk(),menus=[route],answers=['Hello'],responses=['Dịch'],**kwargs)
    self.assertEqual(r['translationCalls'][0]['text'],'Hello')
 def test_txt_and_unicode_preserve_source(self):
  source='    Nguyễn Ánh 😎 — "A" \\path\n2.052.000 ₫ <x>'
  r=run(WORKFLOW,disk=disk(),incoming=File('sample.txt','\ufeff'+source+'\r\n'),responses=['Dịch'])
  self.assertEqual(r['translationCalls'][0]['text'],source)
 def test_convert_text_file_extracts_content_instead_of_renaming_binary(self):
  r=run(WORKFLOW,disk=disk(),incoming=File('notes.md','# Hello\n123'),menus=['yes'],answers=['Hello 123'],responses=['Dịch'])
  self.assertEqual(r['translationCalls'][0]['text'],'Hello 123');self.assertEqual(r['writes'],[])
 def test_html_conversion_extracts_plain_text_before_review(self):
  r=run(WORKFLOW,disk=disk(),incoming=File('page.html','<p>Hello &amp; world</p>'),menus=['yes'],answers=['Hello & world'],responses=['Dịch'])
  self.assertEqual(r['translationCalls'][0]['text'],'Hello & world')
 def test_binary_and_unsupported_files_never_reach_translation(self):
  for name in ('archive.zip','document.docx','movie.mp4','opaque.bin'):
   with self.subTest(name=name):
    r=run(WORKFLOW,disk=disk(),incoming=File(name,'PK\x00binary'))
    self.assertEqual(r['translationCalls'],[]);self.assertIn(STRINGS['vi']['unsupported'],r['previews']);self.assertEqual(r['writes'],[])
 def test_binary_content_in_fake_txt_is_rejected(self):
  r=run(WORKFLOW,disk=disk(),incoming=File('bad.txt','PK\x00binary'))
  self.assertEqual(r['translationCalls'],[]);self.assertIn(STRINGS['vi']['invalidText'],r['previews'])
 def test_multiple_images_and_text_keep_order(self):
  r=run(WORKFLOW,disk=disk(),incoming=['Intro',Image('1.png','One'),Image('2.png','Two')],answers=['Intro\nOne\nTwo'],responses=['Dịch'])
  self.assertEqual(r['translationCalls'][0]['text'],'Intro\nOne\nTwo')
 def test_more_than_ten_input_items_are_not_silently_truncated(self):
  r=run(WORKFLOW,disk=disk(),incoming=[Image(str(i),'text') for i in range(11)])
  self.assertEqual(r['ocrCalls'],[]);self.assertEqual(r['translationCalls'],[]);self.assertIn(STRINGS['vi']['tooMany'],r['previews'])

class PDFTests(unittest.TestCase):
 def test_text_pdf_extracts_all_selected_pages_without_ocr(self):
  pdf=PDF('digital.pdf',[Page('First'),Page('Second')])
  r=run(WORKFLOW,disk=disk(),incoming=pdf,menus=['auto','all'],answers=['First\nSecond'],responses=['Dịch'])
  self.assertEqual(len(r['pdfTextCalls']),2);self.assertEqual(r['ocrCalls'],[]);self.assertEqual(r['translationCalls'][0]['text'],'First\nSecond')
 def test_mixed_pdf_ocr_only_scanned_pages_and_keep_page_order(self):
  pdf=PDF('mixed.pdf',[Page('First'),Page('','Second scan'),Page('Third')])
  r=run(WORKFLOW,disk=disk(),incoming=pdf,menus=['auto',[2,0,1]],answers=['First\nSecond scan\nThird'],responses=['Dịch'])
  self.assertEqual(r['renderedPages'],['mixed-page2.pdf']);self.assertEqual(r['translationCalls'][0]['text'],'First\nSecond scan\nThird')
 def test_force_ocr_ignores_incomplete_text_layer(self):
  pdf=PDF('scan.pdf',[Page('Heading only','Heading and main body')])
  r=run(WORKFLOW,disk=disk(),incoming=pdf,menus=['ocr','all'],answers=['Heading and main body'],responses=['Dịch'])
  self.assertEqual(r['pdfTextCalls'],[]);self.assertEqual(len(r['ocrCalls']),1)
 def test_blank_pdf_page_is_reported_and_manual_correction_allowed(self):
  r=run(WORKFLOW,disk=disk(),incoming=PDF('blank.pdf',[Page('','')]),menus=['auto','all'],answers=['Entered by hand'],responses=['Dịch'])
  self.assertEqual(r['translationCalls'][0]['text'],'Entered by hand');self.assertTrue(any(STRINGS['vi']['noPageText'] in p for p in r['previews']))
 def test_page_selection_retry_limits_without_rendering_rejected_selection(self):
  pdf=PDF('large.pdf',[Page('Page '+str(i)) for i in range(12)])
  r=run(WORKFLOW,disk=disk(),incoming=pdf,menus=['auto','all',[1,5]],answers=['Selected two pages'],responses=['Dịch'])
  self.assertEqual(len(r['pdfTextCalls']),2);self.assertIn(STRINGS['vi']['pageLimit'],r['previews'])
 def test_pdf_over_two_hundred_pages_is_rejected_before_rendering(self):
  r=run(WORKFLOW,disk=disk(),incoming=PDF('huge.pdf',[Page('')]*201),menus=['auto'])
  self.assertEqual(r['renderedPages'],[]);self.assertEqual(r['translationCalls'],[]);self.assertIn(STRINGS['vi']['pdfLimit'],r['previews'])

class TranslationTests(unittest.TestCase):
 def test_fixed_source_and_native_target_codes_are_passed(self):
  r=run(WORKFLOW,disk=disk(cfg(source='en',target='ja')),incoming='Hello',responses=['こんにちは'])
  self.assertEqual(r['translationCalls'][0],{'text':'Hello','target':'ja_JP','source':'en_US'});self.assertEqual(r['detected'],[])
 def test_same_language_and_english_variants_do_not_call_unsupported_pair(self):
  for source,target in [('vi','vi'),('en','en-GB'),('en-GB','en')]:
   with self.subTest(source=source,target=target):
    r=run(WORKFLOW,disk=disk(cfg(source=source,target=target)),incoming='Text 123')
    self.assertEqual(r['translationCalls'],[]);self.assertEqual(r['variables']['Translation'],'Text 123')
 def test_all_catalog_targets_pass_correct_native_identifiers(self):
  for code,desc in LANGUAGES.items():
   with self.subTest(code=code):
    r=run(WORKFLOW,disk=disk(cfg(target=code)),incoming='Hello',ios_version='27.0',detections=['French' if code!='fr' else 'English'],responses=['result'])
    self.assertEqual(r['translationCalls'][0]['target'],desc['apple'])
 def test_ios_version_filters_catalog(self):
  r=run(WORKFLOW,disk=disk());self.assertNotIn('hi',r['variables']['LanguageNames']);self.assertIn('ar',r['variables']['LanguageNames'])
  r=run(WORKFLOW,disk=disk(),ios_version='27.0');self.assertIn('hi',r['variables']['LanguageNames'])
 def test_long_chunks_reassemble_original_without_loss_including_graphemes(self):
  source=('    Nguyễn Á 😎 👨‍👩‍👧‍👦 <tag> 123\n\n'*300).rstrip('\n')
  r=run(WORKFLOW,disk=disk(),incoming=source,responses=[lambda text,target,source:text]*40)
  chunks=[c['text'] for c in r['translationCalls']]
  self.assertEqual(''.join(chunks),source);self.assertGreater(len(chunks),1)
  self.assertTrue(all(not c.startswith('\u200d') for c in chunks));self.assertEqual(r['shown'],[])
 def test_empty_reply_never_becomes_complete_or_saved(self):
  r=run(WORKFLOW,disk=disk(),incoming='Hello',responses=[''])
  self.assertEqual(r['variables']['Route'],'partialActions');self.assertEqual(r['writes'],[]);self.assertEqual(r['variables']['Translation'],'')
 def test_retry_resumes_only_unfinished_section(self):
  source='first '*200+'second '*180+'third '*150
  r=run(WORKFLOW,disk=disk(),incoming=source,menus=['send'],responses=['First','','Second','Third'])
  sent=[c['text'] for c in r['translationCalls']]
  self.assertEqual(sent[1],sent[2]);self.assertNotEqual(sent[0],sent[1]);self.assertEqual(r['variables']['Translation'],'First\nSecond\nThird')
 def test_native_translation_failure_does_not_report_success(self):
  r=run(WORKFLOW,disk=disk(),incoming='Hello')
  self.assertEqual(r['status'],'translation-error');self.assertEqual(r['previews'],[]);self.assertEqual(r['writes'],[])
 def test_echoed_names_or_code_are_valid_translation_results(self):
  r=run(WORKFLOW,disk=disk(),incoming='Nguyễn Ánh 123',responses=['Nguyễn Ánh 123'])
  self.assertEqual(r['variables']['Translation'],'Nguyễn Ánh 123');self.assertEqual(r['variables']['Route'],'resultActions')
 def test_long_ocr_can_edit_one_section_without_changing_the_rest(self):
  source='a'*7000
  r=run(WORKFLOW,disk=disk(),incoming=Image('long.png',source),menus=['editSections','2','prepare'],answers=['B'*3000],responses=['Dịch']*10)
  sent=''.join(c['text'] for c in r['translationCalls'])
  self.assertEqual(sent,'a'*3000+'B'*3000+'a'*1000)
 def test_oversized_input_is_available_for_editing_without_translation(self):
  r=run(WORKFLOW,disk=disk(),incoming='a'*24001)
  self.assertEqual(r['translationCalls'],[]);self.assertIn(STRINGS['vi']['tooLong'],r['previews']);self.assertEqual(r['variables']['SourceText'],'a'*24001)

class ResultAndStorageTests(unittest.TestCase):
 def test_long_result_and_bilingual_text_open_in_quick_look(self):
  translated='Dịch dài 😎 <tag>\n'*1000
  r=run(WORKFLOW,disk=disk(),incoming='Hello',menus=['bilingual'],responses=[translated])
  self.assertTrue(any(translated.rstrip('\n') in body for body in r['previews']));self.assertEqual(r['shown'],[])
  self.assertTrue(any('Hello' in body and 'Dịch dài' in body for body in r['previews']))
 def test_only_explicit_copy_modifies_clipboard(self):
  normal=run(WORKFLOW,disk=disk(),incoming='Hello',responses=['Xin chào'])
  copied=run(WORKFLOW,disk=disk(),incoming='Hello',menus=['copy'],responses=['Xin chào'])
  self.assertEqual(normal['copied'],[]);self.assertEqual(copied['copied'],['Xin chào']);self.assertEqual(copied['writes'],[])
 def test_no_save_leaves_no_private_content_files(self):
  initial=disk();r=run(WORKFLOW,disk=initial,incoming='Private source',responses=['Private translation'])
  self.assertEqual(r['writes'],[]);self.assertEqual(r['disk'],initial)
 def test_explicit_save_and_offline_reuse_before_language_detection(self):
  first=run(WORKFLOW,disk=disk(),incoming='Hello',menus=['saveRecord'],responses=['Xin chào'],rewrite_json=True)
  paths=[p for p in first['writes'] if '/records/' in p];self.assertEqual(len(paths),1)
  again=run(WORKFLOW,disk=first['disk'],incoming='Hello',rewrite_json=True)
  self.assertEqual(again['translationCalls'],[]);self.assertEqual(again['detected'],[]);self.assertEqual(again['requests'],[])
  self.assertEqual(again['variables']['Translation'],'Xin chào');self.assertEqual(again['variables']['ResultOrigin'],'saved')
 def test_double_save_writes_record_once(self):
  r=run(WORKFLOW,disk=disk(),incoming='Hello',menus=['saveRecord','saveRecord'],responses=['Xin chào'])
  self.assertEqual(len([p for p in r['writes'] if '/records/' in p]),1);self.assertIn(STRINGS['vi']['alreadySaved'],r['shown'])
 def test_tampered_translation_is_not_reused(self):
  item=record();item['targetText']='Changed';r=run(WORKFLOW,disk=add_record(disk(),item),incoming='Hello',responses=['New'])
  self.assertEqual(len(r['translationCalls']),1);self.assertEqual(r['variables']['Translation'],'New')
 def test_fresh_result_replacement_requires_confirmation_and_keeps_backup(self):
  item=record();initial=add_record(disk(),item)
  skipped=run(WORKFLOW,disk=initial,incoming='Hello',menus=['startTranslation','saveRecord','back'],responses=['New'])
  self.assertEqual(skipped['writes'],[])
  saved=run(WORKFLOW,disk=initial,incoming='Hello',menus=['startTranslation','saveRecord','yes'],responses=['New'])
  self.assertEqual(json.loads(saved['disk']['QuickTranslation/records/'+item['id']+'.json'].body)['targetText'],'New')
  self.assertEqual(json.loads(saved['disk']['QuickTranslation/backups/'+item['id']+'.json'].body)['targetText'],'Xin chào')
 def test_other_target_uses_original_not_previous_translation(self):
  r=run(WORKFLOW,disk=disk(),incoming='Original text',menus=['targetJob','ja'],responses=['Bản dịch thứ nhất','訳文'])
  self.assertEqual([c['text'] for c in r['translationCalls']],['Original text']*2)
  self.assertEqual(r['translationCalls'][1]['target'],'ja_JP');self.assertEqual(json.loads(r['disk']['QuickTranslation/settings.json'].body)['target'],'ja')
 def test_literal_history_search_accepts_regex_characters(self):
  item=record('Literal \\E [x].*','Translated');r=run(WORKFLOW,disk=add_record(disk(),item),menus=['history',item['id']],answers=['\\E [x].*'])
  self.assertEqual(r['variables']['Translation'],'Translated');self.assertEqual(r['translationCalls'],[])
 def test_history_ignores_staging_and_corrupt_files(self):
  item=record();d=add_record(disk(),item)
  d['QuickTranslation/records/'+item['id']+'.pending.json']=file('pending.json',item);d['QuickTranslation/records/bad.json']=File('bad.json','{bad')
  r=run(WORKFLOW,disk=d,menus=['history','back'],answers=[''])
  self.assertEqual(len(r['menus'][1]['options']),2);self.assertEqual(r['requests'],[])
 def test_hundred_saved_records_have_distinct_rows(self):
  d=disk()
  for i in range(100):d=add_record(d,record('Same prefix '*8+str(i),'Result '+str(i)))
  r=run(WORKFLOW,disk=d,menus=['history','back'],answers=[''])
  self.assertEqual(len(r['menus'][1]['options']),101);self.assertEqual(len(set(r['menus'][1]['options'])),101)
 def test_speech_and_exports_preserve_private_storage(self):
  r=run(WORKFLOW,disk=disk(),incoming='Hello',menus=['speak','export','exportPDF','export','exportBoth','export','share'],responses=['Xin chào'])
  self.assertEqual(r['spoken'],['Xin chào']);self.assertEqual(len(r['exports']),2);self.assertTrue(r['exports'][0].name.endswith('.pdf'))
  self.assertIn('Hello',r['exports'][0].body);self.assertEqual(r['shared'][0].body,'Xin chào');self.assertEqual(r['writes'],[]);self.assertEqual(r['copied'],[])
 def test_source_and_target_preferences_are_remembered(self):
  first=run(WORKFLOW,disk=disk(),menus=['settings','sourceDefault','en','targetDefault','ja'])
  again=run(WORKFLOW,disk=first['disk'],incoming='Hello',responses=['こんにちは'])
  self.assertEqual(again['translationCalls'][0]['source'],'en_US');self.assertEqual(again['translationCalls'][0]['target'],'ja_JP')
 def test_auto_detected_same_language_keeps_original(self):
  r=run(WORKFLOW,disk=disk(),incoming='Xin chào 123',detections=['vi_VN'])
  self.assertEqual(r['translationCalls'],[]);self.assertEqual(r['variables']['Translation'],'Xin chào 123')

class ResourceTests(unittest.TestCase):
 def test_cached_launch_needs_no_github(self):
  r=run(WORKFLOW,disk=disk());self.assertEqual(r['requests'],[]);self.assertEqual(r['writes'],[])
 def test_initial_resource_downloads_do_not_claim_backup_recovery(self):
  r=run(WORKFLOW,network=network('vi'),menus=['vi','vi'])
  self.assertNotIn(STRINGS['vi']['recovered'],r['previews'])
 def test_language_switch_fetches_only_missing_selected_pack(self):
  r=run(WORKFLOW,disk=disk(),menus=['settings','ui','en'],network=network('en'))
  self.assertEqual(r['requests'],[BASE+'ui/en.json']);self.assertEqual(r['variables']['UI'],'en')
  self.assertEqual(json.loads(r['disk']['QuickTranslation/settings.json'].body)['ui'],'en')
 def test_cached_language_switch_is_offline(self):
  initial=disk();initial['QuickTranslation/ui.en.json']=file('ui.en.json',PACKS['en'])
  r=run(WORKFLOW,disk=initial,menus=['settings','ui','en'])
  self.assertEqual(r['requests'],[]);self.assertEqual(r['variables']['UI'],'en')
 def test_failed_language_download_can_return_to_old_interface(self):
  initial=disk();r=run(WORKFLOW,disk=initial,menus=['settings','ui','en','back'],network={BASE+'ui/en.json':'<html>503</html>'})
  self.assertEqual(r['disk'],initial);self.assertEqual(r['variables']['UI'],'vi');self.assertEqual(r['variables']['Route'],'settings')
 def test_bad_resource_downloads_never_replace_current_cache(self):
  broken_catalog=[]
  for field,value in [('_product','bad'),('_schema','999'),('names','{}'),('apple','{"vi":"vi_VN"}'),('minIOS','{"vi":"18"}'),('aliases','[]')]:
   d=dict(CATALOG);d[field]=value;broken_catalog.append(d)
  broken_catalog+=['{bad','<html>403</html>',json.dumps(CATALOG).replace('"_product":','"names":',1)]
  for bad in broken_catalog:
   with self.subTest(value=str(bad)[:100]):
    initial=disk();r=run(WORKFLOW,disk=initial,menus=['settings','updateResources','back'],network={BASE+'catalog.json':bad})
    self.assertEqual(r['disk'],initial);self.assertEqual(r['translationCalls'],[]);self.assertEqual(r['variables']['Route'],'settings')
 def test_malformed_ui_pack_preserves_existing_config_and_catalog(self):
  bad=dict(PACKS['en']);bad['_locale']='vi'
  initial=disk();r=run(WORKFLOW,disk=initial,menus=['settings','ui','en','back'],network={BASE+'ui/en.json':bad})
  self.assertEqual(r['disk'],initial);self.assertEqual(r['variables']['Strings']['main'],STRINGS['vi']['main'])
 def test_update_new_ui_revision_then_restart_offline(self):
  catalog=copy.deepcopy(CATALOG);catalog['_revision']='20261102.1';revisions=json.loads(catalog['revisions']);revisions['vi']='20261102.1';catalog['revisions']=json.dumps(revisions)
  pack={**PACKS['vi'],'_revision':'20261102.1','main':'Giao diện đã cập nhật'}
  r=run(WORKFLOW,disk=disk(),menus=['settings','updateResources'],network={BASE+'catalog.json':catalog,BASE+'ui/vi.json':pack},rewrite_json=True)
  self.assertEqual(r['variables']['Strings']['main'],'Giao diện đã cập nhật');self.assertIn(STRINGS['vi']['updated'],r['shown'])
  again=run(WORKFLOW,disk=r['disk']);self.assertEqual(again['requests'],[]);self.assertEqual(again['variables']['Strings']['main'],'Giao diện đã cập nhật')
 def test_new_interface_can_be_added_via_catalog_without_rebuilding_shortcut(self):
  catalog=copy.deepcopy(CATALOG);catalog['_revision']='20261102.1'
  for field,value in [('locales','Français'),('revisions',CATALOG['_revision'])]:
   d=json.loads(catalog[field]);d['fr']=value;catalog[field]=json.dumps(d,ensure_ascii=False)
  pack={**PACKS['en'],'_locale':'fr','main':'Choisir le contenu'}
  r=run(WORKFLOW,disk=disk(),menus=['settings','updateResources','ui','fr'],network={BASE+'catalog.json':catalog,BASE+'ui/fr.json':pack})
  self.assertEqual(r['variables']['UI'],'fr');self.assertEqual(r['variables']['Strings']['main'],'Choisir le contenu')
  self.assertEqual(r['requests'],[BASE+'catalog.json',BASE+'ui/fr.json'])
 def test_catalog_language_extension_is_dynamic_and_version_filtered(self):
  catalog=copy.deepcopy(CATALOG);catalog['_revision']='future-fixture'
  for field,value in [('names','Fixture language'),('apple','zz_ZZ'),('speech','zz-ZZ'),('minIOS','99')]:
   d=json.loads(catalog[field]);d['zz']=value;catalog[field]=json.dumps(d)
  r=run(WORKFLOW,disk=disk(),menus=['settings','updateResources'],network={BASE+'catalog.json':catalog})
  self.assertNotIn('zz',r['variables']['LanguageNames'])
  again=run(WORKFLOW,disk=r['disk'],ios_version='99.0')
  self.assertIn('zz',again['variables']['LanguageNames'])
 def test_corrupt_primary_ui_is_repaired_from_valid_backup(self):
  initial=disk();initial['QuickTranslation/ui.vi.previous.json']=initial['QuickTranslation/ui.vi.json'];initial['QuickTranslation/ui.vi.json']=File('ui.vi.json','{bad')
  r=run(WORKFLOW,disk=initial)
  self.assertEqual(r['requests'],[]);self.assertIn(STRINGS['vi']['recovered'],r['previews']);self.assertEqual(json.loads(r['disk']['QuickTranslation/ui.vi.json'].body),PACKS['vi'])
 def test_catalog_stage_and_final_corruption_recover_without_private_data_loss(self):
  catalog={**CATALOG,'_revision':'20261102.1'};revs=json.loads(catalog['revisions']);revs['vi']='20261102.1';catalog['revisions']=json.dumps(revs)
  pack={**PACKS['vi'],'_revision':'20261102.1'}
  for path in ('QuickTranslation/catalog.pending.json','QuickTranslation/catalog.json','QuickTranslation/ui.vi.pending.json','QuickTranslation/ui.vi.json'):
   with self.subTest(path=path):
    initial=add_record(disk(),record())
    def corrupt(name,obj):
     if name==path:
      d=json.loads(obj.body);d['_schema']='bad';return file(obj.name,d)
     return obj
    r=run(WORKFLOW,disk=initial,menus=['settings','updateResources'],network={BASE+'catalog.json':catalog,BASE+'ui/vi.json':pack},corrupt_save=corrupt)
    self.assertNotIn(STRINGS['vi']['updated'],r['shown']);self.assertEqual(r['disk']['QuickTranslation/settings.json'],initial['QuickTranslation/settings.json'])
    for p in initial:
     if '/records/' in p:self.assertEqual(r['disk'][p],initial[p])
    again=run(WORKFLOW,disk=r['disk'])
    self.assertEqual(again['requests'],[]);self.assertEqual(again['variables']['Route'],'main')
 def test_stale_valid_catalog_readback_is_detected(self):
  catalog={**CATALOG,'_revision':'20261102.1'}
  def stale(path,obj):return file(obj.name,CATALOG) if path=='QuickTranslation/catalog.pending.json' else obj
  initial=disk();r=run(WORKFLOW,disk=initial,menus=['settings','updateResources'],network={BASE+'catalog.json':catalog},corrupt_save=stale)
  self.assertEqual(r['disk']['QuickTranslation/catalog.json'],initial['QuickTranslation/catalog.json']);self.assertNotIn(STRINGS['vi']['updated'],r['shown'])
 def test_lost_network_never_changes_existing_files(self):
  initial=add_record(disk(),record());r=run(WORKFLOW,disk=initial,menus=['settings','updateResources'])
  self.assertEqual(r['status'],'network-error');self.assertEqual(r['disk'],initial)

class DurabilityAndHelpTests(unittest.TestCase):
 def test_failed_settings_stage_does_not_replace_current(self):
  initial=disk();r=run(WORKFLOW,disk=initial,menus=['settings','targetDefault','ja'],fail_save='QuickTranslation/settings.pending.json')
  self.assertEqual(r['disk']['QuickTranslation/settings.json'],initial['QuickTranslation/settings.json']);self.assertEqual(r['status'],'io-error')
 def test_corrupt_record_stage_never_creates_final_record(self):
  item=record();path='QuickTranslation/staging/'+item['id']+'.json'
  r=run(WORKFLOW,disk=disk(),incoming='Hello',menus=['saveRecord'],responses=['Xin chào'],corrupt_save=path)
  self.assertNotIn('QuickTranslation/records/'+item['id']+'.json',r['disk']);self.assertNotIn(STRINGS['vi']['saved'],r['shown'])
 def test_about_and_all_guides_use_full_quick_look_text(self):
  for code in ('vi','en'):
   with self.subTest(code=code):
    r=run(WORKFLOW,disk=disk(cfg(ui=code)),menus=['info','about','help','guideInputs','guidePDF','guideScreen','guideOffline','guideData'])
    self.assertEqual(r['previews'],[STRINGS[code][key] for key in ('aboutBody','guideInputs','guidePDF','guideScreen','guideOffline','guideData')])
    self.assertEqual(r['shown'],[]);self.assertEqual(r['requests'],[])
 def test_capture_helper_takes_screen_before_any_ui_and_passes_same_image(self):
  image=Image('screen.png','Helo')
  helper=run(SCREEN,screenshot=image)
  self.assertEqual(helper['trace'][0],'takescreenshot');self.assertEqual(helper['calledWorkflows'],[{'name':MAIN_NAME,'input':image}])
  r=run(WORKFLOW,disk=disk(),incoming=helper['calledWorkflows'][0]['input'],answers=['Hello'],responses=['Xin chào'])
  self.assertEqual(r['ocrCalls'],['screen.png']);self.assertEqual(r['translationCalls'][0]['text'],'Hello');self.assertEqual(r['writes'],[])
 def test_capture_first_setup_keeps_image_during_download_and_setup(self):
  image=Image('screen.png','Hello')
  r=run(WORKFLOW,incoming=image,network=network('vi'),menus=['vi','vi'],answers=['Hello'],responses=['Xin chào'])
  self.assertEqual(r['ocrCalls'],['screen.png']);self.assertEqual(r['translationCalls'][0]['text'],'Hello')
 def test_no_embedded_languages_or_credentials_or_recursive_main(self):
  encoded=json.dumps(WORKFLOW,ensure_ascii=False)
  for code in STRINGS:
   for key in ('main','guideInputs','guideScreen','guideData'):self.assertNotIn(STRINGS[code][key],encoded)
  ids=[a['WFWorkflowActionIdentifier'] for a in WORKFLOW['WFWorkflowActions']]
  for kind in ('runworkflow','alert','showwebpage','runjavascript','base64encode','openurl','savetocameraroll'):
   self.assertNotIn('is.workflow.actions.'+kind,ids)
  self.assertNotIn('deepseek',encoded.lower());self.assertNotIn('crossDeviceItemID',encoded)


class AdditionalBoundaryTests(unittest.TestCase):
 def test_oversized_pdf_rejected_before_split_or_ocr(self):
  r=run(WORKFLOW,disk=disk(),incoming=PDF('large.pdf',[Page('text')],size=26000000))
  self.assertEqual(r['pdfTextCalls'],[]);self.assertEqual(r['ocrCalls'],[]);self.assertEqual(r['translationCalls'],[])
  self.assertIn(STRINGS['vi']['fileTooLarge'],r['previews'])
 def test_image_limit_applies_across_multiple_image_bundles(self):
  incoming=[[Image(str(i)+'.png','Text') for i in range(6)],[Image(str(i+6)+'.png','Text') for i in range(6)]]
  r=run(WORKFLOW,disk=disk(),incoming=incoming,menus=['image','image'],answers=[''])
  self.assertEqual(len(r['ocrCalls']),10);self.assertEqual(r['translationCalls'],[]);self.assertIn(STRINGS['vi']['tooMany'],r['previews'])
 def test_unsupported_ios_stops_with_readable_guidance(self):
  r=run(WORKFLOW,ios_version='17.7')
  self.assertEqual(r['requests'],[]);self.assertEqual(r['translationCalls'],[]);self.assertTrue(any('iOS 18' in p for p in r['previews']))
 def test_unavailable_source_and_target_are_reconfigured_safely(self):
  r=run(WORKFLOW,disk=disk(cfg(source='xx',target='zz')),menus=['ja'])
  saved=json.loads(r['disk']['QuickTranslation/settings.json'].body)
  self.assertEqual((saved['source'],saved['target']),('auto','ja'));self.assertEqual(r['translationCalls'],[])
 def test_saved_removed_language_can_be_viewed_then_retranslated_to_supported_target(self):
  item=record(target='zz',source_lang='xx')
  r=run(WORKFLOW,disk=add_record(disk(),item),menus=['history',item['id'],'startTranslation','ja'],answers=[''],responses=['New Japanese result'])
  self.assertEqual(r['translationCalls'][0]['target'],'ja_JP');self.assertEqual(r['translationCalls'][0]['source'],'Detected language')
  self.assertEqual(r['variables']['JobSource'],'auto');self.assertEqual(r['variables']['Translation'],'New Japanese result')
 def test_catalog_with_no_supported_languages_is_rejected_before_commit(self):
  catalog=copy.deepcopy(CATALOG);catalog['_revision']='future-only';minimum=json.loads(catalog['minIOS']);catalog['minIOS']=json.dumps({k:'99' for k in minimum})
  initial=disk();r=run(WORKFLOW,disk=initial,menus=['settings','updateResources','back'],network={BASE+'catalog.json':catalog})
  self.assertEqual(r['disk'],initial);self.assertTrue(r['variables']['LanguageNames']);self.assertEqual(r['variables']['Route'],'settings')
 def test_catalog_removing_current_target_prompts_for_a_replacement(self):
  catalog=copy.deepcopy(CATALOG);catalog['_revision']='remove-fixture'
  for field in ('names','apple','speech','minIOS'):
   mapping=json.loads(catalog[field]);mapping.pop('vi');catalog[field]=json.dumps(mapping,ensure_ascii=False)
  r=run(WORKFLOW,disk=disk(cfg(source='en')),menus=['settings','updateResources','ja'],network={BASE+'catalog.json':catalog})
  saved=json.loads(r['disk']['QuickTranslation/settings.json'].body)
  self.assertEqual((saved['source'],saved['target']),('en','ja'));self.assertNotIn('vi',r['variables']['LanguageNames'])


class SourceFallbackTests(unittest.TestCase):
 def test_unclear_detection_can_choose_source_before_translation(self):
  r=run(WORKFLOW,disk=disk(),incoming='Ambiguous text',menus=['en'],detections=['Unknown language'],responses=['Dịch'])
  self.assertEqual(r['translationCalls'][0]['source'],'en_US');self.assertEqual(r['translationCalls'][0]['text'],'Ambiguous text')
  self.assertEqual(r['variables']['SourceLang'],'auto');self.assertEqual(r['variables']['JobSource'],'en')
 def test_accepting_auto_after_empty_detection_does_not_loop(self):
  r=run(WORKFLOW,disk=disk(),incoming='Ambiguous text',menus=['auto'],detections=[''],responses=['Dịch'])
  self.assertEqual(len(r['detected']),1);self.assertEqual(len(r['translationCalls']),1);self.assertEqual(r['translationCalls'][0]['source'],'Detected language')
 def test_numbers_and_symbols_skip_language_detection_and_translation(self):
  r=run(WORKFLOW,disk=disk(),incoming='2.052.000 ₫ 😎 +84 90 123')
  self.assertEqual(r['detected'],[]);self.assertEqual(r['translationCalls'],[]);self.assertEqual(r['variables']['Translation'],'2.052.000 ₫ 😎 +84 90 123')
  self.assertEqual(r['variables']['ResultOrigin'],'original')
 def test_result_source_change_reuses_original_and_can_save_valid_new_identity(self):
  r=run(WORKFLOW,disk=disk(),incoming='Original text',menus=['sourceJob','en','saveRecord'],responses=['First','Second'])
  self.assertEqual([c['text'] for c in r['translationCalls']],['Original text']*2);self.assertEqual(r['translationCalls'][1]['source'],'en_US')
  paths=[p for p in r['writes'] if '/records/' in p];self.assertEqual(len(paths),1)
  saved=json.loads(r['disk'][paths[0]].body);self.assertEqual(saved['sourceLang'],'en');self.assertEqual(saved['sourceText'],'Original text')

if __name__=='__main__':
 result=unittest.main(exit=False,verbosity=2).result
 report={'version':VERSION,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'nativeDeviceVerified':False,'liveAppleTranslationCalls':0,'ocrIsSimulated':True,'PDFNativeIOIsSimulated':True,'screenCaptureIsSimulated':True}
 (ROOT/'qa/test-results.json').write_text(json.dumps(report,indent=2)+'\n')
 raise SystemExit(0 if result.wasSuccessful() else 1)
