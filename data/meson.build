desktop_file = i18n.merge_file(
  input: APP_ID + '.desktop.in',
  output: APP_ID + '.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: get_option('datadir') / 'applications'
)

metainfo_file = i18n.merge_file(
  input: APP_ID + '.metainfo.xml.in',
  output: APP_ID + '.metainfo.xml',
  po_dir: '../po',
  install: true,
  install_dir: get_option('datadir') / 'metainfo'
)

install_data(APP_ID + '.gschema.xml',
  install_dir: get_option('datadir') / 'glib-2.0' / 'schemas'
)

subdir('icons')
subdir('ui')
