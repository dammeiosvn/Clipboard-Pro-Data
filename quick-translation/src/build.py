"""Compile native Apple translation workflows; no runtime Python or JavaScript."""
from pathlib import Path
from contextlib import contextmanager
import json,hashlib,plistlib
from workflow import Workflow,dictionary_value,variable as v,ref,token
ROOT=Path(__file__).resolve().parents[1]
VERSION='1.0-beta1'
MAIN_NAME='Quick-Translation'
SCREEN_NAME='Quick-Translation-Screen'
BASE='https://raw.githubusercontent.com/dammeiosvn/Clipboard-Pro-Data/main/quick-translation/resources/v1/'
JS=r'"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"'
JSNZ=JS.replace(')*"',')+"')
ID=r'[a-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,2}'
CODE=r'\A'+ID+r'\z'
REV=r'\A[A-Za-z0-9._-]{1,32}\z'
HASH=r'\A[0-9a-f]{64}\z'
SETTINGS_KEYS='product schema ui source target revision'.split()
RECORD_KEYS='product schema id sourceHash targetHash sourceText targetText sourceLang targetLang detectedSource engine engineRevision createdAt inputKind'.split()
CATALOG_KEYS='_product _schema _revision locales revisions names apple speech minIOS aliases'.split()
FOLDER={'fileLocation':{'WFFileLocationType':'Shortcuts','relativeSubpath':'','appContainerBundleIdentifier':'com.apple.shortcuts','fileProviderDomainID':'com.apple.CloudDocs.MobileDocumentsFileProvider'},'filename':'Documents','displayName':'Shortcuts'}
NOW={'Type':'CurrentDate','Aggrandizements':[{'Type':'WFDateFormatVariableAggrandizement','WFDateFormatStyle':'Custom','WFISO8601IncludeTime':False,'WFDateFormat':'yyyy-MM-dd HH:mm:ss Z'}]}
IMAGE_TYPE=r'(?i)\A(?:Image|Photo|Ảnh|Hình ảnh|Bild|Imagen|Immagine|Imagem|Изображение|画像|图像|影像|圖片|이미지|รูปภาพ|Gambar|Görüntü|صورة|छवि|Obraz|Afbeelding)\z'
TEXT_TYPE=r'(?i)\A(?:Text|Rich text|Văn bản|Văn bản đa dạng thức|Texte|Texto|Testo|Tekst|Текст|テキスト|文本|文字|텍스트|ข้อความ|Teks|Metin|نص|पाठ)\z'
PDF_TYPE=r'(?i)\A(?:PDF|PDF document|Tài liệu PDF|Document PDF)\z'
CHUNKS=r'(?s)(?:\X){1,1200}\z|(?:\X){1,1200}(?<=\n\n)|(?:\X){1,1200}(?<=\s)|(?:\X){1,1200}'
EDIT_CHUNKS=CHUNKS.replace('1200','3000')
BOOT_ERROR='Chưa đọc được gói ngôn ngữ. Kiểm tra mạng/iCloud rồi thử lại. Dữ liệu cũ vẫn được giữ.\n\nLanguage resources unavailable. Check internet/iCloud and retry. Existing data is kept.'
BOOT_SAVE='Chưa xác minh được tệp tài nguyên vừa lưu. Hãy chạy lại.\nThe resource file could not be verified. Please run again.'

def fixed_object(keys,value=JS):
 field=r'"(?:'+'|'.join(keys)+r')"\s*:\s*'+value
 return r'\A\s*\{\s*'+field+r'(?:\s*,\s*'+field+r'){'+str(len(keys)-1)+r'}\s*\}\s*\z'
def flat_map(key=r'"'+ID+r'"',value=JSNZ,maximum=64):
 field=key+r'\s*:\s*'+value
 return r'\A\s*\{\s*'+field+r'(?:\s*,\s*'+field+r'){0,'+str(maximum-1)+r'}\s*\}\s*\z'

def build():
 labels=json.loads((ROOT/'config/strings.json').read_text())['vi']
 ui_keys=['_product','_schema','_revision','_locale',*labels]
 w=Workflow(MAIN_NAME);a,get,text,put,L=w.action,w.get,w.text,w.put,w.label
 @contextmanager
 def branch(route):
  g=w.if_eq(v('PassRoute'),route);yield;w.end_if(g)
 def raw(x):return a('detect.text',{'WFInput':ref(x)},'Text contents')
 def preview(*parts):
  file=w.named_json(text(*parts),'Quick-Translation.txt')
  return a('previewdocument',{'WFInput':ref(file)},'Read full text in Quick Look')
 def message(key,stop=False):
  preview(L(key))
  if stop:a('exit')
 def short_notice(key):a('showresult',{'Text':token(L(key))},'Short confirmation')
 def read(name):return a('documentpicker.open',{'WFFile':ref(v('StorageRoot')),'WFGetFilePath':token('QuickTranslation/',name),'WFFileErrorIfNotFound':False,'WFGetFolderContents':False},'Read local file')
 def mkdir(path='QuickTranslation'):return a('file.createfolder',{'WFFolder':ref(v('StorageRoot')),'WFFilePath':path},'Local folder')
 def save(body,name):return a('documentpicker.save',{'WFInput':ref(body),'WFFolder':ref(v('StorageRoot')),'WFAskWhereToSave':False,'WFFileDestinationPath':token('QuickTranslation/',name),'WFSaveFileOverwrite':True},'Save local file')
 def norm(source):return w.replace(w.replace(w.replace(text(source),r'\r\n?','\n'),r'\A\uFEFF',''),r'\A[\r\n]+|[\r\n]+\z','')
 def nonblank(x):return w.if_text(w.replace(x,r'\s',''))
 def lower(x):return a('text.changecase',{'text':token(x),'WFCaseType':'lowercase','Show-text':True},'Lowercase identifier')
 def exists(source,key):
  keys=w.keys(source);w.assign('KeyCount','0');populated=w.if_has(keys)
  lines=a('text.combine',{'text':ref(keys),'WFTextSeparator':'New Lines'},'Dictionary keys')
  w.set('KeyCount',w.count(w.match(lines,r'(?m)^\Q',key,r'\E$')));w.end_if(populated)
  return w.if_gt(v('KeyCount'))
 def require(value,expected,code):
  good=w.if_eq(text('v:',value),text('v:',expected));w.otherwise(good);preview(L('saveFailed'),'\n',code);a('exit');w.end_if(good)
 def start():w.empty_list('Rows');w.empty_dict('RowMap')
 def row(label,identifier):w.append('Rows',label);w.set('RowMap',put(v('RowMap'),w.hash(label),identifier))
 def finish(prompt):return text(get(v('RowMap'),w.hash(text(w.choose(v('Rows'),prompt)))))
 def menu(items,prompt=None):
  start()
  for icon,key,route in items:row(text(icon,' ',L(key)),text(route))
  return finish(prompt or L('title'))
 def choose_language(current,source=False):
  start()
  if source:row(text('🌐 ',L('auto')),text('auto'))
  loop,code=w.each(w.keys(v('LanguageNames')))
  w.set('LanguageRow',get(v('LanguageNames'),code));same=w.if_eq(code,current);w.set('LanguageRow',text('✓ ',v('LanguageRow')));w.end_if(same)
  row(v('LanguageRow'),code);w.end_loop(loop)
  return finish(L('source' if source else 'target'))
 def key_hash(data):
  sorted_keys=a('filter.files',{'WFContentItemInputParameter':ref(w.keys(data)),'WFContentItemSortProperty':'Name','WFContentItemSortOrder':'A to Z'},'Sorted schema keys')
  return w.hash(a('text.combine',{'text':ref(sorted_keys),'WFTextSeparator':'New Lines'},'Canonical keys'))
 def settings_candidate(source):
  w.assign('SettingsOK','0');body=raw(source);guards=[w.if_match(body,fixed_object(SETTINGS_KEYS))]
  data=a('detect.dictionary',{'WFInput':ref(body)},'Validated settings JSON')
  guards +=[w.if_eq(w.count(w.keys(data)),str(len(SETTINGS_KEYS))),w.if_eq(get(data,'product'),'quick-translation'),w.if_eq(get(data,'schema'),'1'),w.if_match(get(data,'ui'),CODE),w.if_match(get(data,'source'),r'\A(?:auto|'+ID+r')\z'),w.if_match(get(data,'target'),CODE),w.if_match(get(data,'revision'),HASH)]
  w.set('SettingsCandidate',data);w.assign('SettingsOK','1')
  for g in reversed(guards):w.end_if(g)
 def catalog_candidate(source):
  w.assign('CatalogOK','0');body=raw(source)
  guards=[w.if_match(body,r'(?s)\A.{1,100000}\z'),w.if_match(body,fixed_object(CATALOG_KEYS,JSNZ))]
  data=a('detect.dictionary',{'WFInput':ref(body)},'Validated resource catalog')
  guards +=[w.if_eq(w.count(w.keys(data)),str(len(CATALOG_KEYS))),w.if_eq(get(data,'_product'),'quick-translation-catalog'),w.if_eq(get(data,'_schema'),'1'),w.if_match(get(data,'_revision'),REV)]
  specs=[('locales','Locales',r'"'+ID+r'"',JSNZ,32),('revisions','Revisions',r'"'+ID+r'"',r'"[A-Za-z0-9._-]{1,32}"',32),('names','Names',r'"'+ID+r'"',JSNZ,64),('apple','Apple',r'"'+ID+r'"',r'"[a-z]{2,3}_[A-Z]{2}"',64),('speech','Speech',r'"'+ID+r'"',r'"[a-z]{2,3}-[A-Za-z0-9-]{2,20}"',64),('minIOS','MinIOS',r'"'+ID+r'"',r'"[0-9]{2}"',64),('aliases','Aliases',JSNZ,r'"'+ID+r'"',200)]
  for field,var,key,val,maximum in specs:
   body_map=get(data,field);guards.append(w.if_match(body_map,flat_map(key,val,maximum)))
   mapping=a('detect.dictionary',{'WFInput':ref(body_map)},'Validated catalog '+field)
   pairs=w.count(w.match(body_map,r'(?<=[{,])\s*'+key+r'\s*:\s*'+val));guards.append(w.if_eq(w.count(w.keys(mapping)),pairs))
   w.set('Cand'+var,mapping)
  guards.append(w.if_eq(key_hash(v('CandLocales')),key_hash(v('CandRevisions'))))
  for var in ('Apple','Speech','MinIOS'):guards.append(w.if_eq(key_hash(v('CandNames')),key_hash(v('Cand'+var))))
  w.set('CatalogCandidate',data);w.assign('CatalogOK','1')
  for g in reversed(guards):w.end_if(g)
 def ui_candidate(source):
  w.assign('UIOK','0');body=raw(source)
  guards=[w.if_match(body,r'(?s)\A.{1,100000}\z'),w.if_match(body,fixed_object(ui_keys,JSNZ))]
  data=a('detect.dictionary',{'WFInput':ref(body)},'Validated interface JSON')
  guards +=[w.if_eq(w.count(w.keys(data)),str(len(ui_keys))),w.if_eq(get(data,'_product'),'quick-translation-ui'),w.if_eq(get(data,'_schema'),'1'),w.if_eq(get(data,'_locale'),v('RequestedUI')),w.if_eq(get(data,'_revision'),get(v('WorkRevisions'),v('RequestedUI')))]
  w.set('UICandidate',data);w.assign('UIOK','1')
  for g in reversed(guards):w.end_if(g)
 def check_next(kind,body,success,failure):
  w.set('ResourceInput',body);w.assign('ResourceSuccess',success);w.assign('ResourceFailure',failure);w.assign('Route','validate'+kind)
 def work_catalog():
  w.set('WorkCatalog',v('CatalogCandidate'))
  for name in ('Locales','Revisions','Names','Apple','Speech','MinIOS','Aliases'):w.set('Work'+name,v('Cand'+name))
 def settings_save(after):w.assign('SettingsAfter',after);w.assign('Route','saveSettings')
 def cache_id(source_hash,source,target):return w.hash(text(source_hash,'|',source,'|',target,'|apple-translate|1'))
 def record_candidate(source):
  w.assign('RecordOK','0');body=raw(source);guards=[w.if_match(body,fixed_object(RECORD_KEYS))]
  data=a('detect.dictionary',{'WFInput':ref(body)},'Validated saved translation')
  guards +=[w.if_eq(w.count(w.keys(data)),str(len(RECORD_KEYS))),w.if_eq(get(data,'product'),'quick-translation-record'),w.if_eq(get(data,'schema'),'1'),w.if_match(get(data,'id'),HASH),w.if_match(get(data,'sourceHash'),HASH),w.if_match(get(data,'targetHash'),HASH),w.if_match(get(data,'sourceLang'),r'\A(?:auto|'+ID+r')\z'),w.if_match(get(data,'targetLang'),CODE),w.if_eq(get(data,'engine'),'apple-translate'),w.if_eq(get(data,'engineRevision'),'1'),w.if_match(get(data,'inputKind'),r'\A(?:text|images|mixed|manual|clipboard|file|pdf)\z')]
  guards +=[nonblank(get(data,'sourceText')),nonblank(get(data,'targetText')),w.if_eq(w.hash(get(data,'sourceText')),get(data,'sourceHash')),w.if_eq(w.hash(get(data,'targetText')),get(data,'targetHash')),w.if_eq(cache_id(get(data,'sourceHash'),get(data,'sourceLang'),get(data,'targetLang')),get(data,'id'))]
  w.set('RecordCandidate',data);w.assign('RecordOK','1')
  for g in reversed(guards):w.end_if(g)
 def bind_record():
  for var,key in [('SourceText','sourceText'),('Translation','targetText'),('JobSource','sourceLang'),('JobTarget','targetLang'),('DetectedSource','detectedSource'),('SourceKind','inputKind'),('CacheID','id')]:w.set(var,get(v('RecordCandidate'),key))
  w.assign('SavedFlag','1');w.assign('ResultOrigin','saved')
 def new_job(kind):
  w.set('JobSource',v('SourceLang'));w.set('JobTarget',v('TargetLang'));w.assign('SourceKind',kind);w.assign('SavedFlag','0');w.assign('ResultReturn','main')
 def translation_title():
  w.set('TargetName',v('JobTarget'));known=exists(v('LanguageNames'),v('JobTarget'));w.set('TargetName',get(v('LanguageNames'),v('JobTarget')));w.end_if(known)
  return text(v('DetectedSource'),' → ',v('TargetName'))
 # Startup never reads the clipboard and never writes source text to disk.
 a('comment',{'WFCommentActionText':'© Sentechtipsvn\nNative Apple translation, local OCR and Quick Look. Data-only GitHub resources are cached in iCloud. Save translation content only on explicit request. No API key, JavaScript, WebView or recursive restart.'})
 boot={'version':VERSION,'values':{}}
 resources=a('dictionary',{'WFItems':dictionary_value(boot)},'Program constants');top=len(w.actions)-1
 w.set('Config',resources);w.set('Constants',get(v('Config'),'values'));w.assign('EmptyText','');w.enable_constants('Constants','EmptyText')
 w.set('StorageRoot',a('file',{'WFFile':FOLDER},'Portable Shortcuts iCloud folder'))
 for name,value in [('UI','vi'),('RequestedUI','vi'),('UIChosen','0'),('SourceLang','auto'),('TargetLang','vi'),('SettingsValid','0'),('SettingsRevision','0'),('SettingsRecovered','0'),('ResourcesRecovered','0'),('ActiveReady','0'),('NeedCatalogWrite','0'),('NeedUIWrite','0'),('ResourceBack','cancel'),('SourceText',''),('Translation',''),('ResultReturn','main')]:w.assign(name,value)
 w.set('Inbound',{'Type':'ExtensionInput'});w.assign('StartupRoute','main');shared=w.if_has(v('Inbound'));w.assign('StartupRoute','shared');w.end_if(shared)
 w.set('AfterSetupTarget',v('StartupRoute'));w.assign('AfterResources','startupResources')
 version=a('getdevicedetails',{'WFDeviceDetail':'System Version'},'Installed iOS version');w.set('IOSMajor',w.first(w.match(raw(version),r'\A[0-9]+')))
 old_ios=w.if_gt(text('18'),v('IOSMajor'));preview(text('Cần iOS 18 trở lên. / Requires iOS 18 or later.'));a('exit');w.end_if(old_ios)
 settings_candidate(read('settings.json'));good=w.if_eq(v('SettingsOK'),'1');w.otherwise(good);settings_candidate(read('settings.previous.json'));recovered=w.if_eq(v('SettingsOK'),'1');w.assign('SettingsRecovered','1');w.end_if(recovered);w.end_if(good)
 good=w.if_eq(v('SettingsOK'),'1')
 for name,key in [('UI','ui'),('RequestedUI','ui'),('SourceLang','source'),('TargetLang','target'),('SettingsRevision','revision')]:w.set(name,get(v('SettingsCandidate'),key))
 w.set('ActiveSettings',v('SettingsCandidate'));w.assign('SettingsValid','1');w.assign('UIChosen','1');w.end_if(good)
 w.assign('Route','loadCatalog');loop=w.times(320);w.set('PassRoute',v('Route'))
 with branch('loadCatalog'):
  check_next('Catalog',read('catalog.json'),'catalogLoaded','previousCatalog')
 with branch('previousCatalog'):
  check_next('Catalog',read('catalog.previous.json'),'catalogRecovered','fetchCatalog')
 with branch('catalogRecovered'):
  w.assign('ResourcesRecovered','1');w.assign('NeedCatalogWrite','1');w.assign('Route','catalogLoaded')
 with branch('validateCatalog'):
  catalog_candidate(v('ResourceInput'));good=w.if_eq(v('CatalogOK'),'1');w.set('Route',v('ResourceSuccess'));w.otherwise(good);w.set('Route',v('ResourceFailure'));w.end_if(good)
 with branch('fetchCatalog'):
  download=a('downloadurl',{'WFURL':BASE+'catalog.json','WFHTTPMethod':'GET'},'Download data-only catalog')
  check_next('Catalog',download,'catalogDownloaded','resourceBad')
 with branch('catalogDownloaded'):
  w.assign('NeedCatalogWrite','1');w.assign('Route','catalogLoaded')
 with branch('catalogLoaded'):
  work_catalog();w.empty_dict('WorkSupportedNames')
  each,code=w.each(w.keys(v('WorkNames')));too_new=w.if_gt(get(v('WorkMinIOS'),code),v('IOSMajor'));w.otherwise(too_new);w.set('WorkSupportedNames',put(v('WorkSupportedNames'),code,get(v('WorkNames'),code)));w.end_if(too_new);w.end_loop(each)
  w.assign('NeedUIWrite','0');w.assign('Route','loadUI')
  configured=w.if_eq(v('UIChosen'),'1');known=exists(v('WorkLocales'),v('RequestedUI'));w.otherwise(known);w.assign('Route','chooseUI');w.end_if(known);w.otherwise(configured);w.assign('Route','chooseUI');w.end_if(configured)
  available=w.if_has(w.keys(v('WorkSupportedNames')));w.otherwise(available);w.assign('Route','resourceBad');w.end_if(available)
 with branch('chooseUI'):
  start();each,code=w.each(w.keys(v('WorkLocales')));row(get(v('WorkLocales'),code),code);w.end_loop(each)
  w.set('RequestedUI',finish(text('🌐 Ngôn ngữ / Language\nCần mạng lần đầu / Internet needed once')));w.assign('UIChosen','1');w.assign('Route','loadUI')
 with branch('loadUI'):
  check_next('UI',read(text('ui.',v('RequestedUI'),'.json')),'uiLoaded','previousUI')
 with branch('previousUI'):
  check_next('UI',read(text('ui.',v('RequestedUI'),'.previous.json')),'uiRecovered','fetchUI')
 with branch('uiRecovered'):
  w.assign('ResourcesRecovered','1');w.assign('NeedUIWrite','1');w.assign('Route','uiLoaded')
 with branch('fetchUI'):
  allowed=exists(v('WorkLocales'),v('RequestedUI'))
  download=a('downloadurl',{'WFURL':token(BASE,'ui/',v('RequestedUI'),'.json'),'WFHTTPMethod':'GET'},'Download only the selected interface')
  check_next('UI',download,'uiDownloaded','resourceBad');w.otherwise(allowed);w.assign('Route','resourceBad');w.end_if(allowed)
 with branch('validateUI'):
  ui_candidate(v('ResourceInput'));good=w.if_eq(v('UIOK'),'1');w.set('Route',v('ResourceSuccess'));w.otherwise(good);w.set('Route',v('ResourceFailure'));w.end_if(good)
 with branch('uiDownloaded'):
  w.assign('NeedUIWrite','1');w.assign('Route','uiLoaded')
 with branch('uiLoaded'):
  w.set('WorkUI',v('UICandidate'));w.assign('Route','commitResources')
 with branch('commitResources'):
  needed=w.if_eq(v('NeedUIWrite'),'1');w.assign('Route','stageUI');w.otherwise(needed);w.assign('Route','maybeStageCatalog');w.end_if(needed)
 with branch('stageUI'):
  mkdir();save(v('WorkUI'),text('ui.',v('RequestedUI'),'.pending.json'))
  check_next('UI',read(text('ui.',v('RequestedUI'),'.pending.json')),'writeUI','resourceSaveFailed')
 with branch('writeUI'):
  w.assign('UIBackupDone','0');active=w.if_eq(v('ActiveReady'),'1');same=w.if_eq(get(v('ActiveUI'),'_locale'),v('RequestedUI'));save(v('ActiveUI'),text('ui.',v('RequestedUI'),'.previous.json'));w.assign('UIBackupDone','1');w.end_if(same);w.end_if(active)
  save(v('WorkUI'),text('ui.',v('RequestedUI'),'.json'));check_next('UI',read(text('ui.',v('RequestedUI'),'.json')),'uiWritten','resourceSaveFailed')
 with branch('uiWritten'):
  backed=w.if_eq(v('UIBackupDone'),'1');w.otherwise(backed);save(v('WorkUI'),text('ui.',v('RequestedUI'),'.previous.json'));w.end_if(backed)
  w.assign('NeedUIWrite','0');w.assign('Route','maybeStageCatalog')
 with branch('maybeStageCatalog'):
  needed=w.if_eq(v('NeedCatalogWrite'),'1');mkdir();save(v('WorkCatalog'),'catalog.pending.json');check_next('Catalog',read('catalog.pending.json'),'writeCatalog','resourceSaveFailed');w.otherwise(needed);w.assign('Route','resourcesReady');w.end_if(needed)
 with branch('writeCatalog'):
  matched=w.if_eq(get(v('CatalogCandidate'),'_revision'),get(v('WorkCatalog'),'_revision'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'locales'),get(v('WorkCatalog'),'locales'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'revisions'),get(v('WorkCatalog'),'revisions'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'names'),get(v('WorkCatalog'),'names'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'apple'),get(v('WorkCatalog'),'apple'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'speech'),get(v('WorkCatalog'),'speech'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'minIOS'),get(v('WorkCatalog'),'minIOS'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'aliases'),get(v('WorkCatalog'),'aliases'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  active=w.if_eq(v('ActiveReady'),'1');save(v('ActiveCatalog'),'catalog.previous.json');w.end_if(active)
  save(v('WorkCatalog'),'catalog.json');check_next('Catalog',read('catalog.json'),'catalogWritten','resourceSaveFailed')
 with branch('catalogWritten'):
  matched=w.if_eq(get(v('CatalogCandidate'),'_revision'),get(v('WorkCatalog'),'_revision'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'locales'),get(v('WorkCatalog'),'locales'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'revisions'),get(v('WorkCatalog'),'revisions'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'names'),get(v('WorkCatalog'),'names'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'apple'),get(v('WorkCatalog'),'apple'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'speech'),get(v('WorkCatalog'),'speech'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'minIOS'),get(v('WorkCatalog'),'minIOS'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  matched=w.if_eq(get(v('CatalogCandidate'),'aliases'),get(v('WorkCatalog'),'aliases'));w.otherwise(matched);preview(text(BOOT_SAVE),'\nQT302');a('exit');w.end_if(matched)
  active=w.if_eq(v('ActiveReady'),'1');w.otherwise(active);save(v('WorkCatalog'),'catalog.previous.json');w.end_if(active)
  w.assign('NeedCatalogWrite','0');w.assign('Route','resourcesReady')
 with branch('resourcesReady'):
  w.set('Strings',v('WorkUI'));w.set('ActiveUI',v('WorkUI'));w.set('ActiveCatalog',v('WorkCatalog'));w.set('UI',v('RequestedUI'))
  for name in ('Locales','Revisions','Names','Apple','Speech','MinIOS','Aliases'):w.set('Active'+name,v('Work'+name))
  w.set('LanguageNames',v('WorkSupportedNames'))
  w.set('LanguageApple',v('WorkApple'));w.set('LanguageSpeech',v('WorkSpeech'));w.set('LanguageAliases',v('WorkAliases'));w.assign('ActiveReady','1');w.set('Route',v('AfterResources'))
  for flag in ('SettingsRecovered','ResourcesRecovered'):
   recovered=w.if_eq(v(flag),'1');message('recovered');w.assign(flag,'0');w.end_if(recovered)
 with branch('resourceBad'):
  preview(text(BOOT_ERROR));start();row(text('↻ Thử lại / Retry'),text('retry'));row(text('↩️ Quay lại / Back'),text('back'));choice=finish(text('Quick Translation'))
  retry=w.if_eq(choice,'retry');w.assign('Route','fetchCatalog');w.otherwise(retry);w.assign('Route','resourceAbort');w.end_if(retry)
 with branch('resourceAbort'):
  active=w.if_eq(v('ActiveReady'),'1')
  w.set('WorkCatalog',v('ActiveCatalog'));w.set('WorkUI',v('ActiveUI'));w.set('WorkSupportedNames',v('LanguageNames'));w.set('RequestedUI',v('UI'))
  for name in ('Locales','Revisions','Names','Apple','Speech','MinIOS','Aliases'):w.set('Work'+name,v('Active'+name))
  w.assign('NeedCatalogWrite','0');w.assign('NeedUIWrite','0');w.assign('Route','settings');w.otherwise(active);a('exit');w.end_if(active)
 with branch('resourceSaveFailed'):
  preview(text(BOOT_SAVE),'\nQT301');a('exit')
 with branch('startupResources'):
  w.set('Route',v('StartupRoute'));w.set('AfterSetupTarget',v('StartupRoute'))
  configured=w.if_eq(v('SettingsValid'),'1')
  w.assign('PrefsNeedSave','0')
  automatic=w.if_eq(v('SourceLang'),'auto');w.otherwise(automatic);supported=exists(v('LanguageNames'),v('SourceLang'));w.otherwise(supported);w.assign('SourceLang','auto');w.assign('PrefsNeedSave','1');w.end_if(supported);w.end_if(automatic)
  supported=exists(v('LanguageNames'),v('TargetLang'));changed=w.if_eq(v('PrefsNeedSave'),'1');settings_save(v('StartupRoute'));w.end_if(changed)
  w.otherwise(supported);message('adjusted');w.assign('Route','setupTarget');w.end_if(supported)
  w.otherwise(configured);w.assign('Route','setupTarget');w.end_if(configured)
 with branch('setupTarget'):
  w.set('TargetLang',choose_language(v('TargetLang')));settings_save(v('AfterSetupTarget'))
 with branch('saveSettings'):
  w.set('NewRevision',w.hash(text(v('UI'),v('SourceLang'),v('TargetLang'),v('SettingsRevision'),NOW)))
  data=a('dictionary',{'WFItems':dictionary_value({'product':'quick-translation','schema':'1','ui':v('UI'),'source':v('SourceLang'),'target':v('TargetLang'),'revision':v('NewRevision')})},'New settings')
  mkdir();save(data,'settings.pending.json');settings_candidate(read('settings.pending.json'));require(v('SettingsOK'),'1','QT101');require(get(v('SettingsCandidate'),'revision'),v('NewRevision'),'QT101')
  old=w.if_eq(v('SettingsValid'),'1');save(v('ActiveSettings'),'settings.previous.json');w.end_if(old)
  save(data,'settings.json');settings_candidate(read('settings.json'));require(v('SettingsOK'),'1','QT102')
  for key,value in [('ui',v('UI')),('source',v('SourceLang')),('target',v('TargetLang')),('revision',v('NewRevision'))]:require(get(v('SettingsCandidate'),key),value,'QT102')
  w.set('ActiveSettings',v('SettingsCandidate'));w.set('SettingsRevision',v('NewRevision'));w.assign('SettingsValid','1');w.set('Route',v('SettingsAfter'))
 with branch('main'):
  w.set('Route',menu([('📋','clipboard','clipboard'),('⌨️','manual','manual'),('🖼️','photos','photos'),('📷','camera','camera'),('📂','files','files'),('🕘','history','history'),('⚙️','settings','settings'),('ℹ️','info','info'),('✖','cancel','cancel')],L('main')))
 with branch('shared'):
  w.set('RawInputs',v('Inbound'));new_job('text');w.assign('Route','collect')
 with branch('clipboard'):
  w.set('RawInputs',a('getclipboard',{},'Clipboard explicitly requested'));new_job('clipboard');w.assign('Route','collect')
 with branch('manual'):
  w.set('SourceText',raw(a('ask',{'WFInputType':'Text','WFAskActionPrompt':token(L('enterText')),'WFAllowsMultilineText':True},'Entered text')));new_job('manual');w.assign('Route','prepare')
 for route in ('photos','camera','files'):
  with branch(route):
   if route=='photos':selected=a('selectphoto',{'WFSelectMultiplePhotos':True},'Choose images')
   elif route=='camera':selected=a('takephoto',{'WFCameraCaptureShowPreview':True,'WFCameraCaptureDevice':'Back','WFPhotoCount':1},'Camera image')
   else:selected=a('file.select',{'SelectMultiple':True},'Choose documents or images')
   w.set('RawInputs',selected);new_job('images' if route!='files' else 'file');w.assign('Route','collect')
 with branch('collect'):
  w.empty_list('InputTexts');w.empty_list('MissingPages');w.empty_list('PageBudget');w.empty_list('ImageBudget');w.assign('MissingImages','0');w.assign('CollectFailed','0');w.assign('NeedReview','0');w.assign('SawImage','0');w.assign('SawText','0');w.assign('SawPDF','0');w.assign('Route','main')
  many=w.if_gt(w.count(v('RawInputs')),10);message('tooMany');w.otherwise(many)
  each,item=w.each(v('RawInputs'));active=w.if_eq(v('CollectFailed'),'0')
  w.set('InputItem',item);kind=raw(a('getitemtype',{'WFInput':ref(v('InputItem'))},'Content type'));w.assign('InputMode','unknown');w.assign('InputWasPDF','0')
  image=w.if_match(kind,IMAGE_TYPE);w.assign('InputMode','image');w.end_if(image)
  txt=w.if_match(kind,TEXT_TYPE);w.assign('InputMode','text');w.end_if(txt)
  pdf=w.if_match(kind,PDF_TYPE);w.assign('InputMode','file');w.assign('InputWasPDF','1');w.end_if(pdf)
  file=w.if_match(kind,r'(?i)\A(?:File|Tệp|Document|Tài liệu|Datei|Archivo|Fichier|ファイル|文件|파일)\z');w.assign('InputMode','file');w.end_if(file)
  unknown=w.if_eq(v('InputMode'),'unknown');w.set('InputMode',menu([('🖼️','asImage','image'),('📂','asFile','file'),('📝','asText','text'),('↩️','skip','skip')],L('unknownInput')));w.end_if(unknown)
  # File metadata is inspected before any attempt to decode file content.
  file=w.if_eq(v('InputMode'),'file')
  extension=lower(raw(a('properties.files',{'WFFolder':ref(v('InputItem')),'WFContentItemPropertyName':'File Extension'},'File extension')));w.set('FileExtension',extension)
  size=a('properties.files',{'WFFolder':ref(v('InputItem')),'WFContentItemPropertyName':'File Size'},'File size in bytes')
  huge=w.if_gt(size,25000000);message('fileTooLarge');w.assign('CollectFailed','1');w.assign('InputMode','skip');w.otherwise(huge)
  w.assign('InputMode','unsupported')
  for pattern,mode in [(r'\Apdf\z','pdf'),(r'\Atxt\z','text'),(r'\A(?:png|jpe?g|heic|heif|tiff?|webp|bmp|gif)\z','image'),(r'\A(?:md|csv|json|log|ini|ya?ml|xml|html?|rtf)\z','convert')]:
   matched=w.if_match(v('FileExtension'),pattern);w.assign('InputMode',mode);w.end_if(matched)
  was_pdf=w.if_eq(v('InputWasPDF'),'1');w.assign('InputMode','pdf');w.end_if(was_pdf)
  w.end_if(huge);w.end_if(file)
  unsupported=w.if_eq(v('InputMode'),'unsupported');message('unsupported');w.assign('CollectFailed','1');w.end_if(unsupported)
  converting=w.if_eq(v('InputMode'),'convert')
  message('convertPrompt');choice=menu([('📄','convert','yes'),('↩️','skip','skip')],L('files'))
  yes=w.if_eq(choice,'yes');w.set('ConvertedText',raw(v('InputItem')))
  html=w.if_match(v('FileExtension'),r'\Ahtml?\z');w.set('ConvertedText',raw(a('getrichtextfromhtml',{'WFHTML':token(v('ConvertedText'))},'HTML to plain text')));w.end_if(html)
  converted=w.named_json(v('ConvertedText'),'Converted.txt');w.set('InputItem',converted);w.assign('NeedReview','1');w.assign('InputMode','text')
  w.otherwise(yes);w.assign('InputMode','skip');w.end_if(yes);w.end_if(converting)
  image=w.if_eq(v('InputMode'),'image');w.assign('NeedReview','1');w.assign('SawImage','1')
  images=a('detect.images',{'WFInput':ref(v('InputItem'))},'Images in selected content')
  too_many_images=w.if_gt(w.count(images),10);message('tooMany');w.assign('CollectFailed','1');w.otherwise(too_many_images)
  picture_loop,picture=w.each(images);image_active=w.if_eq(v('CollectFailed'),'0');w.append('ImageBudget',text('1'));over_images=w.if_gt(w.count(v('ImageBudget')),10);message('tooMany');w.assign('CollectFailed','1');w.otherwise(over_images);extracted=raw(a('extracttextfromimage',{'WFImage':ref(picture)},'On-device OCR'))
  present=nonblank(extracted);w.append('InputTexts',extracted);w.otherwise(present);w.assign('MissingImages','1');w.end_if(present);w.end_if(over_images);w.end_if(image_active);w.end_loop(picture_loop);w.end_if(too_many_images);w.end_if(image)
  txt=w.if_eq(v('InputMode'),'text');w.assign('SawText','1');w.set('ExtractedText',norm(raw(v('InputItem'))))
  bad=w.if_match(v('ExtractedText'),r'[\x00\uFFFD][\s\S]*');message('invalidText');w.assign('CollectFailed','1');w.otherwise(bad)
  present=nonblank(v('ExtractedText'));w.append('InputTexts',v('ExtractedText'));w.end_if(present);w.end_if(bad);w.end_if(txt)
  pdf=w.if_eq(v('InputMode'),'pdf');w.assign('SawPDF','1');w.assign('NeedReview','1')
  w.set('PDFMode',menu([('📄','pdfAuto','auto'),('🔎','pdfOCR','ocr')],L('pdfMode')))
  w.set('PDFPages',a('splitpdf',{'WFInput':ref(v('InputItem'))},'PDF pages in document order'))
  enormous=w.if_gt(w.count(v('PDFPages')),200);message('pdfLimit');w.assign('CollectFailed','1');w.otherwise(enormous)
  start();w.empty_list('PageCounter');page_loop,page=w.each(v('PDFPages'));w.append('PageCounter',text('1'));index=text(w.count(v('PageCounter')));row(text(L('page'),' ',index),index);w.end_loop(page_loop)
  w.set('PDFRowMap',v('RowMap'));w.assign('PageSelectionOK','0')
  selection_attempts=w.times(3);needed=w.if_eq(v('PageSelectionOK'),'0')
  picked=a('choosefromlist',{'WFInput':ref(v('Rows')),'WFChooseFromListActionPrompt':token(L('pages')),'WFChooseFromListActionSelectMultiple':True,'WFChooseFromListActionSelectAll':True},'Choose PDF pages')
  many_pages=w.if_gt(w.count(picked),10);message('pageLimit');w.otherwise(many_pages)
  some=w.if_has(picked);w.empty_dict('SelectedPages');selection_loop,selection=w.each(picked);number=get(v('PDFRowMap'),w.hash(raw(selection)));w.set('SelectedPages',put(v('SelectedPages'),number,text('1')));w.end_loop(selection_loop);w.assign('PageSelectionOK','1');w.end_if(some);w.end_if(many_pages);w.end_if(needed);w.end_loop(selection_attempts)
  valid_selection=w.if_eq(v('PageSelectionOK'),'1');w.empty_list('PageCounter')
  page_loop,page=w.each(v('PDFPages'));w.append('PageCounter',text('1'));w.set('PageNumber',text(w.count(v('PageCounter'))))
  chosen=exists(v('SelectedPages'),v('PageNumber'));active_page=w.if_eq(v('CollectFailed'),'0');w.append('PageBudget',text('1'))
  over_budget=w.if_gt(w.count(v('PageBudget')),10);message('pageLimit');w.assign('CollectFailed','1');w.otherwise(over_budget)
  w.assign('PageText','');w.assign('RenderPage','1');automatic=w.if_eq(v('PDFMode'),'auto')
  w.set('PageText',norm(raw(a('gettextfrompdf',{'WFInput':ref(page),'WFCombinePages':True},'Text layer of this PDF page'))));present=nonblank(v('PageText'));w.assign('RenderPage','0');w.end_if(present);w.end_if(automatic)
  render=w.if_eq(v('RenderPage'),'1')
  page_image=a('makeimagefrompdfpage',{'WFInput':ref(page),'WFMakeImageFromPDFPageColorspace':'RGB','WFMakeImageFromPDFPageResolution':'150'},'Render one PDF page for OCR')
  w.set('PageText',norm(raw(a('extracttextfromimage',{'WFImage':ref(page_image)},'OCR of scanned PDF page'))));w.end_if(render)
  present=nonblank(v('PageText'));w.append('InputTexts',text('[',L('page'),' ',v('PageNumber'),']\n',v('PageText')));w.otherwise(present);w.append('MissingPages',text(L('page'),' ',v('PageNumber')));w.end_if(present)
  w.end_if(over_budget);w.end_if(active_page);w.end_if(chosen);w.end_loop(page_loop)
  w.otherwise(valid_selection);w.assign('CollectFailed','1');w.end_if(valid_selection);w.end_if(enormous);w.end_if(pdf)
  w.end_if(active);w.end_loop(each)
  w.assign('SourceText','');some=w.if_has(v('InputTexts'));w.set('SourceText',norm(a('text.combine',{'text':ref(v('InputTexts')),'WFTextSeparator':'New Lines'},'Combined input text')));w.end_if(some)
  image=w.if_eq(v('SawImage'),'1');w.assign('SourceKind','images');mixed=w.if_eq(v('SawText'),'1');w.assign('SourceKind','mixed');w.end_if(mixed);w.end_if(image);pdf=w.if_eq(v('SawPDF'),'1');w.assign('SourceKind','pdf');w.end_if(pdf)
  w.assign('Route','prepare');review=w.if_eq(v('NeedReview'),'1');w.assign('Route','review');w.end_if(review)
  warnings=w.if_has(v('MissingPages'));preview(L('noPageText'),'\n\n',a('text.combine',{'text':ref(v('MissingPages')),'WFTextSeparator':'New Lines'},'Unrecognized PDF pages'));w.end_if(warnings)
  warnings=w.if_eq(v('MissingImages'),'1');message('noImageText');w.end_if(warnings)
  failed=w.if_eq(v('CollectFailed'),'1');w.assign('Route','main');w.end_if(failed);w.end_if(many)
 with branch('review'):
  long=w.if_gt(w.count(v('SourceText'),'Characters'),6000);w.assign('Route','reviewLong')
  w.otherwise(long);w.set('SourceText',raw(a('ask',{'WFInputType':'Text','WFAskActionPrompt':token(L('review')),'WFAskActionDefaultAnswer':token(v('SourceText')),'WFAllowsMultilineText':True},'Reviewed OCR text')));w.assign('Route','prepare');w.end_if(long)
 with branch('reviewLong'):
  preview(L('original'),'\n\n',v('SourceText'));w.assign('Route','reviewLongActions')
 with branch('reviewLongActions'):
  w.set('Route',menu([('📖','viewOriginal','reviewLong'),('✏️','editSections','editSections'),('🌐','continueTranslate','prepare'),('↩️','back','main')],L('reviewLong')))
 with branch('editSections'):
  w.set('EditChunks',w.match(v('SourceText'),EDIT_CHUNKS));start();w.empty_list('SectionCounter')
  each,section=w.each(v('EditChunks'));w.append('SectionCounter',text('1'));index=text(w.count(v('SectionCounter')));snippet=w.first(w.match(w.replace(section,r'\s+',' '),r'[\s\S]{1,50}'));row(text('#',index,' · ',snippet),index);w.end_loop(each)
  w.set('EditSectionID',finish(L('editSections')));w.assign('Route','editSection')
 with branch('editSection'):
  selected=a('getitemfromlist',{'WFInput':ref(v('EditChunks')),'WFItemSpecifier':'Item At Index','WFItemIndex':token(v('EditSectionID'))},'Selected source section')
  w.set('EditedSection',raw(a('ask',{'WFInputType':'Text','WFAskActionPrompt':token(L('editPart')),'WFAskActionDefaultAnswer':token(selected),'WFAllowsMultilineText':True},'Edited section')))
  w.assign('EditedWhole','');w.empty_list('SectionCounter');each,section=w.each(v('EditChunks'));w.append('SectionCounter',text('1'));same=w.if_eq(text(w.count(v('SectionCounter'))),v('EditSectionID'));w.assign('EditedWhole',v('EditedWhole'),v('EditedSection'));w.otherwise(same);w.assign('EditedWhole',v('EditedWhole'),section);w.end_if(same);w.end_loop(each)
  w.set('SourceText',v('EditedWhole'));w.assign('Route','reviewLong')
 with branch('editJob'):
  large=w.if_gt(w.count(v('SourceText'),'Characters'),6000);w.assign('Route','reviewLong');w.otherwise(large)
  w.set('SourceText',raw(a('ask',{'WFInputType':'Text','WFAskActionPrompt':token(L('enterText')),'WFAskActionDefaultAnswer':token(v('SourceText')),'WFAllowsMultilineText':True},'Edited source')));w.assign('Route','prepare');w.end_if(large)
 with branch('prepare'):
  w.set('SourceText',norm(v('SourceText')));w.assign('SavedFlag','0');w.assign('ResultOrigin','apple');w.assign('Route','main')
  present=nonblank(v('SourceText'))
  long=w.if_gt(w.count(v('SourceText'),'Characters'),24000);message('tooLong');w.assign('Route','reviewLong');w.otherwise(long)
  w.set('SourceHash',w.hash(v('SourceText')));w.set('CacheID',cache_id(v('SourceHash'),v('JobSource'),v('JobTarget')))
  record_candidate(read(text('records/',v('CacheID'),'.json')));valid=w.if_eq(v('RecordOK'),'1');same=w.if_eq(get(v('RecordCandidate'),'id'),v('CacheID'));bind_record();w.assign('Route','result');w.otherwise(same);w.assign('Route','startTranslation');w.end_if(same);w.otherwise(valid);w.assign('Route','startTranslation');w.end_if(valid);w.end_if(long)
  w.otherwise(present);message('empty');w.assign('Route','manual');w.end_if(present)
 with branch('startTranslation'):
  target_supported=exists(v('LanguageNames'),v('JobTarget'))
  auto_source=w.if_eq(v('JobSource'),'auto');w.otherwise(auto_source);source_supported=exists(v('LanguageNames'),v('JobSource'));w.otherwise(source_supported);w.assign('JobSource','auto');w.end_if(source_supported);w.end_if(auto_source)
  w.assign('SavedFlag','0');w.assign('Translation','');w.assign('ResultOrigin','apple');w.set('DetectedSource',L('unknownLanguage'));w.assign('DetectedCode','');w.assign('Route','queueTranslation')
  automatic=w.if_eq(v('JobSource'),'auto');has_letters=w.if_match(v('SourceText'),r'\p{L}[\s\S]*')
  w.set('DetectedSource',raw(a('detectlanguage',{'WFInput':ref(text(v('SourceText')))},'Detect source language with Apple')))
  blank=nonblank(v('DetectedSource'));w.otherwise(blank);w.set('DetectedSource',L('unknownLanguage'));w.end_if(blank)
  alias=w.replace(lower(w.replace(v('DetectedSource'),r'\A\s+|\s+\z','')),'_','-');known_alias=exists(v('LanguageAliases'),alias);candidate=get(v('LanguageAliases'),alias);known_language=exists(v('LanguageNames'),candidate);w.set('DetectedCode',candidate);w.set('DetectedSource',get(v('LanguageNames'),candidate));w.end_if(known_language);w.end_if(known_alias)
  unclear=w.if_eq(v('DetectedCode'),'');w.assign('Route','sourceJob');w.end_if(unclear);w.end_if(has_letters)
  w.otherwise(automatic);w.set('DetectedCode',v('JobSource'));w.set('DetectedSource',get(v('LanguageNames'),v('JobSource')));w.end_if(automatic)
  w.otherwise(target_supported);message('adjusted');w.assign('Route','targetJob');w.end_if(target_supported)
 with branch('sourceJob'):
  w.set('JobSource',choose_language(v('JobSource'),True))
  automatic=w.if_eq(v('JobSource'),'auto');w.assign('DetectedCode','');w.set('DetectedSource',L('unknownLanguage'));w.assign('Route','queueTranslation')
  w.otherwise(automatic);w.assign('Route','prepare');w.end_if(automatic)
 with branch('queueTranslation'):
  target_supported=exists(v('LanguageNames'),v('JobTarget'))
  w.assign('SavedFlag','0');w.assign('ResultOrigin','apple');w.set('CacheID',cache_id(w.hash(v('SourceText')),v('JobSource'),v('JobTarget')))
  w.set('Chunks',w.match(v('SourceText'),CHUNKS));w.empty_list('CompletedParts');w.assign('Route','send')
  w.assign('SameLanguage','0');same=w.if_eq(v('DetectedCode'),v('JobTarget'));w.assign('SameLanguage','1');w.end_if(same)
  source_en=w.if_match(v('DetectedCode'),r'\Aen(?:-GB)?\z');target_en=w.if_match(v('JobTarget'),r'\Aen(?:-GB)?\z');w.assign('SameLanguage','1');w.end_if(target_en);w.end_if(source_en)
  same=w.if_eq(v('SameLanguage'),'1');w.set('Translation',v('SourceText'));w.assign('ResultOrigin','original');w.assign('Route','result');w.end_if(same)
  has_letters=w.if_match(v('SourceText'),r'\p{L}[\s\S]*');w.otherwise(has_letters);w.set('Translation',v('SourceText'));w.assign('ResultOrigin','original');w.assign('Route','result');w.end_if(has_letters)
  w.otherwise(target_supported);message('adjusted');w.assign('Route','targetJob');w.end_if(target_supported)
 with branch('send'):
  w.set('NextPart',v('CompletedParts'));w.append('NextPart',text('next'))
  w.set('CurrentChunk',raw(a('getitemfromlist',{'WFInput':ref(v('Chunks')),'WFItemSpecifier':'Item At Index','WFItemIndex':token(w.count(v('NextPart')))},'Unfinished source section')))
  automatic=w.if_eq(v('JobSource'),'auto')
  translated=a('text.translate',{'WFInputText':token(v('CurrentChunk')),'WFSelectedLanguage':ref(get(v('LanguageApple'),v('JobTarget')))},'Apple translation with automatic source')
  w.set('PartTranslation',norm(raw(translated)));w.otherwise(automatic)
  translated=a('text.translate',{'WFInputText':token(v('CurrentChunk')),'WFSelectedLanguage':ref(get(v('LanguageApple'),v('JobTarget'))),'WFSelectedFromLanguage':ref(get(v('LanguageApple'),v('JobSource')))},'Apple translation with chosen source')
  w.set('PartTranslation',norm(raw(translated)));w.end_if(automatic)
  present=nonblank(v('PartTranslation'));w.append('CompletedParts',v('PartTranslation'))
  finished=w.if_eq(w.count(v('CompletedParts')),w.count(v('Chunks')));w.set('Translation',a('text.combine',{'text':ref(v('CompletedParts')),'WFTextSeparator':'New Lines'},'Complete translation'));w.assign('Route','result');w.otherwise(finished);w.assign('Route','send');w.end_if(finished)
  w.otherwise(present);message('translationEmpty');w.assign('Route','partialActions');w.end_if(present)
 with branch('partialActions'):
  start();row(text('↻ ',L('retry')),text('send'));some=w.if_has(v('CompletedParts'));row(text('📄 ',L('partial')),text('partial'));w.end_if(some)
  for icon,key,route in [('✏️','editText','editJob'),('🌐','otherTarget','targetJob'),('↩️','back','main')]:row(text(icon,' ',L(key)),text(route))
  w.set('Route',finish(L('translation')))
 with branch('partial'):
  preview(L('partial'),'\n\n',a('text.combine',{'text':ref(v('CompletedParts')),'WFTextSeparator':'New Lines'},'Completed sections only'));w.assign('Route','partialActions')
 with branch('result'):
  w.set('ResultHeading',L('translation'));cached=w.if_eq(v('ResultOrigin'),'saved');w.set('ResultHeading',L('savedHeading'));w.end_if(cached);unchanged=w.if_eq(v('ResultOrigin'),'original');w.set('ResultHeading',L('original'));w.end_if(unchanged)
  preview(v('ResultHeading'),'\n',translation_title(),'\n\n',v('Translation'));w.assign('Route','resultActions')
 with branch('resultActions'):
  w.set('Route',menu([('📄','view','result'),('📑','bilingual','bilingual'),('📋','copy','copy'),('🔊','speak','speak'),('💾','save','saveRecord'),('🌐','otherTarget','targetJob'),('🔎','changeSource','sourceJob'),('↻','retryFresh','startTranslation'),('✏️','editText','editJob'),('📤','export','export'),('➕','newTranslation','main'),('↩️','back','resultBack')],text(L('title'),'\n',translation_title(),' · ',w.count(v('Translation'),'Characters'),' ',L('chars'))))
 with branch('resultBack'):w.set('Route',v('ResultReturn'))
 with branch('bilingual'):
  preview(L('original'),'\n',v('SourceText'),'\n\n',L('translation'),'\n',v('Translation'));w.assign('Route','resultActions')
 with branch('copy'):
  a('setclipboard',{'WFInput':ref(v('Translation')),'WFLocalOnly':True},'Copy explicitly selected translation');short_notice('copied');w.assign('Route','resultActions')
 with branch('speak'):
  known=exists(v('LanguageSpeech'),v('JobTarget'));a('speaktext',{'WFText':token(v('Translation')),'WFSpeakTextWait':True,'WFSpeakTextLanguage':token(get(v('LanguageSpeech'),v('JobTarget')))},'Speak translation');w.otherwise(known);message('unsupported');w.end_if(known);w.assign('Route','resultActions')
 with branch('targetJob'):
  w.set('JobTarget',choose_language(v('JobTarget')));w.set('TargetLang',v('JobTarget'));settings_save(text('prepare'))
 with branch('export'):
  w.set('Route',menu([('📄','exportTXT','exportTXT'),('📑','exportBoth','exportBoth'),('📝','exportOriginal','exportOriginal'),('📕','exportPDF','exportPDF'),('📤','share','share'),('↩️','back','resultActions')],L('export')))
 for route in ('exportTXT','exportBoth','exportOriginal','exportPDF','share'):
  with branch(route):
   if route=='exportOriginal':body=v('SourceText')
   elif route in ('exportBoth','exportPDF'):body=text(L('original'),'\n',v('SourceText'),'\n\n',L('translation'),'\n',v('Translation'))
   else:body=v('Translation')
   file=w.named_json(body,'Quick-Translation.txt')
   if route=='exportPDF':file=a('makepdf',{'WFInput':ref(file),'WFPDFIncludeMargin':True,'WFPDFDocumentMergeBehavior':'Append'},'Bilingual plain-text PDF')
   if route=='share':a('share',{'WFInput':ref(file)},'User-controlled share sheet')
   else:a('documentpicker.save',{'WFInput':ref(file),'WFAskWhereToSave':True,'WFSaveFileOverwrite':False},'Choose export location')
   w.assign('Route','resultActions')
 with branch('saveRecord'):
  w.assign('Route','resultActions');already=w.if_eq(v('SavedFlag'),'1');short_notice('alreadySaved');w.otherwise(already)
  w.assign('MaySave','1');record_candidate(read(text('records/',v('CacheID'),'.json')))
  old=w.if_eq(v('RecordOK'),'1');message('replaceSave');choice=menu([('💾','replace','yes'),('↩️','back','back')],L('save'));yes=w.if_eq(choice,'yes');w.otherwise(yes);w.assign('MaySave','0');w.end_if(yes);w.end_if(old)
  allowed=w.if_eq(v('MaySave'),'1')
  record=a('dictionary',{'WFItems':dictionary_value({'product':'quick-translation-record','schema':'1','id':v('CacheID'),'sourceHash':w.hash(v('SourceText')),'targetHash':w.hash(v('Translation')),'sourceText':v('SourceText'),'targetText':v('Translation'),'sourceLang':v('JobSource'),'targetLang':v('JobTarget'),'detectedSource':v('DetectedSource'),'engine':'apple-translate','engineRevision':'1','createdAt':text(NOW),'inputKind':v('SourceKind')})},'Explicitly saved translation')
  mkdir('QuickTranslation/records');mkdir('QuickTranslation/staging');save(record,text('staging/',v('CacheID'),'.json'));record_candidate(read(text('staging/',v('CacheID'),'.json')));require(v('RecordOK'),'1','QT201');require(get(v('RecordCandidate'),'id'),v('CacheID'),'QT201');require(get(v('RecordCandidate'),'targetHash'),w.hash(v('Translation')),'QT201')
  old_file=read(text('records/',v('CacheID'),'.json'));old=w.if_has(old_file);mkdir('QuickTranslation/backups');save(old_file,text('backups/',v('CacheID'),'.json'));w.end_if(old)
  save(record,text('records/',v('CacheID'),'.json'));record_candidate(read(text('records/',v('CacheID'),'.json')));require(v('RecordOK'),'1','QT202');require(get(v('RecordCandidate'),'id'),v('CacheID'),'QT202');require(get(v('RecordCandidate'),'targetHash'),w.hash(v('Translation')),'QT202')
  w.assign('SavedFlag','1');short_notice('saved');w.end_if(allowed);w.end_if(already)
 with branch('history'):
  w.set('HistoryQuery',raw(a('ask',{'WFInputType':'Text','WFAskActionPrompt':token(L('query')),'WFAllowsMultilineText':False},'Saved translation query')));w.assign('Route','historyList')
 with branch('historyList'):
  folder=mkdir('QuickTranslation/records');files=a('file.getfoldercontents',{'WFFolder':ref(folder),'Recursive':False},'Saved record files only')
  start();w.empty_list('HistoryCounter');each,file=w.each(files)
  filename=a('getitemname',{'WFInput':ref(file)},'Record filename');normal=w.if_match(filename,r'\A[0-9a-f]{64}(?:\.json)?\z')
  record_candidate(file);valid=w.if_eq(v('RecordOK'),'1');w.assign('SearchMatch','1');query=nonblank(v('HistoryQuery'))
  haystack=text(get(v('RecordCandidate'),'sourceText'),'\n',get(v('RecordCandidate'),'targetText'))
  removed=a('text.replace',{'WFInput':token(haystack),'WFReplaceTextFind':token(v('HistoryQuery')),'WFReplaceTextReplace':'','WFReplaceTextRegularExpression':False,'WFReplaceTextCaseSensitive':False},'Literal text search')
  same=w.if_eq(removed,haystack);w.assign('SearchMatch','0');w.end_if(same);w.end_if(query)
  found=w.if_eq(v('SearchMatch'),'1');snippet=w.first(w.match(w.replace(get(v('RecordCandidate'),'sourceText'),r'\s+',' '),r'[\s\S]{1,55}'))
  w.set('HistoryTarget',get(v('RecordCandidate'),'targetLang'));known=exists(v('LanguageNames'),v('HistoryTarget'));w.set('HistoryTarget',get(v('LanguageNames'),v('HistoryTarget')));w.end_if(known)
  w.append('HistoryCounter',text('1'));row(text(get(v('RecordCandidate'),'createdAt'),' · ',v('HistoryTarget'),'\n',snippet,' · #',w.count(v('HistoryCounter'))),get(v('RecordCandidate'),'id'))
  w.end_if(found);w.end_if(valid);w.end_if(normal);w.end_loop(each)
  some=w.if_has(v('Rows'));ordered=a('filter.files',{'WFContentItemInputParameter':ref(v('Rows')),'WFContentItemSortProperty':'Name','WFContentItemSortOrder':'Z to A'},'Newest saves first');w.set('Rows',ordered);row(text('↩️ ',L('back')),text('back'));chosen=finish(L('search'))
  back=w.if_eq(chosen,'back');w.assign('Route','main');w.otherwise(back);w.set('ChosenRecordID',chosen);w.assign('Route','openRecord');w.end_if(back)
  w.otherwise(some);message('noHistory');w.assign('Route','main');w.end_if(some)
 with branch('openRecord'):
  record_candidate(read(text('records/',v('ChosenRecordID'),'.json')));valid=w.if_eq(v('RecordOK'),'1');bind_record();w.assign('ResultReturn','historyList');w.assign('Route','result');w.otherwise(valid);message('recordGone');w.assign('Route','historyList');w.end_if(valid)
 with branch('settings'):
  w.set('Route',menu([('🌐','target','targetDefault'),('🔎','source','sourceDefault'),('🌍','ui','ui'),('🔄','update','updateResources'),('ℹ️','info','info'),('↩️','back','main')],L('settings')))
 with branch('targetDefault'):
  w.set('TargetLang',choose_language(v('TargetLang')));settings_save(text('settings'))
 with branch('sourceDefault'):
  w.set('SourceLang',choose_language(v('SourceLang'),True));settings_save(text('settings'))
 with branch('ui'):
  start();each,code=w.each(w.keys(v('ActiveLocales')));row(get(v('ActiveLocales'),code),code);w.end_loop(each);row(text('↩️ ',L('back')),text('back'));chosen=finish(L('ui'))
  back=w.if_eq(chosen,'back');w.assign('Route','settings');w.otherwise(back);w.set('RequestedUI',chosen);w.assign('AfterResources','uiCommit');w.assign('ResourceBack','settings');w.assign('NeedUIWrite','0');w.assign('NeedCatalogWrite','0');w.assign('Route','loadUI');w.end_if(back)
 with branch('uiCommit'):settings_save(text('settings'))
 with branch('updateResources'):
  w.assign('AfterResources','resourcesUpdated');w.assign('ResourceBack','settings');w.assign('NeedCatalogWrite','0');w.assign('NeedUIWrite','0');w.assign('Route','fetchCatalog')
 with branch('resourcesUpdated'):
  short_notice('updated');w.assign('AfterSetupTarget','settings')
  target_valid=exists(v('LanguageNames'),v('TargetLang'));settings_save(text('settings'));w.otherwise(target_valid);message('adjusted');w.assign('Route','setupTarget');w.end_if(target_valid)
  automatic=w.if_eq(v('SourceLang'),'auto');w.otherwise(automatic);source_valid=exists(v('LanguageNames'),v('SourceLang'));w.otherwise(source_valid);w.assign('SourceLang','auto');w.end_if(source_valid);w.end_if(automatic)
 with branch('info'):
  w.set('Route',menu([('ℹ️','about','about'),('📖','help','help'),('↩️','back','settings')],L('info')))
 with branch('about'):message('aboutBody');w.assign('Route','info')
 with branch('help'):
  chosen=menu([('📝','helpInputs','guideInputs'),('📕','helpPDF','guidePDF'),('📱','helpScreen','guideScreen'),('🌐','helpOffline','guideOffline'),('💾','helpData','guideData'),('↩️','back','info')],L('help'))
  back=w.if_eq(chosen,'info');w.assign('Route','info');w.otherwise(back);w.set('GuideKey',chosen);w.assign('Route','showGuide');w.end_if(back)
 with branch('showGuide'):preview(get(v('Strings'),v('GuideKey')));w.assign('Route','help')
 with branch('cancel'):a('exit')
 w.end_loop(loop);a('exit')
 boot['values']=w.constants;w.actions[top]['WFWorkflowActionParameters']['WFItems']=dictionary_value(boot)
 workflow=w.header();workflow['WFWorkflowInputContentItemClasses']=['WFImageContentItem','WFStringContentItem','WFRichTextContentItem','WFPDFContentItem','WFGenericFileContentItem'];workflow['WFWorkflowIcon']={'WFWorkflowIconStartColor':431817727,'WFWorkflowIconGlyphNumber':59509}
 return workflow

def build_screen():
 w=Workflow(SCREEN_NAME)
 shot=w.action('takescreenshot',{'WFTakeScreenshotScreenshotType':'Full Screen'},'Current screen before any UI')
 w.action('comment',{'WFCommentActionText':'© Sentechtipsvn\nInstall Quick-Translation first and keep that name. Assign this capture helper to Back Tap or AssistiveTouch. The first action captures the screen without saving it to Photos. Main shortcut handles OCR, review, translation and Quick Look.'})
 w.action('runworkflow',{'WFWorkflowName':MAIN_NAME,'WFInput':ref(shot)},'Send captured image to main shortcut')
 w.action('exit')
 result=w.header();result['WFWorkflowTypes']=[];result['WFWorkflowInputContentItemClasses']=[];result['WFWorkflowHasShortcutInputVariables']=False;result['WFWorkflowIcon']={'WFWorkflowIconStartColor':431817727,'WFWorkflowIconGlyphNumber':59446}
 return result

def main():
 reports={};out=ROOT/'dist';out.mkdir(exist_ok=True)
 for name,workflow in [(MAIN_NAME,build()),(SCREEN_NAME,build_screen())]:
  raw=plistlib.dumps(workflow,fmt=plistlib.FMT_BINARY,sort_keys=False)
  (out/(name+'.unsigned.bplist')).write_bytes(raw);(out/(name+'.unsigned.shortcut')).write_bytes(plistlib.dumps(workflow,sort_keys=False))
  reports[name]={'actions':len(workflow['WFWorkflowActions']),'binaryBytes':len(raw),'unsignedSHA256':hashlib.sha256(raw).hexdigest()}
 report={'version':VERSION,'workflows':reports,'nativeDeviceVerified':False}
 (ROOT/'qa/build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
