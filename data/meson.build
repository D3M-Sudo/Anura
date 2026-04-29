app_id = 'com.github.d3msudo.anura'

desktop_file = i18n.merge_file(
  input: app_id + '.desktop.in',
  output: app_id + '.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file]
  )
endif

appstream_file = i18n.merge_file(
  input: app_id + '.metainfo.xml.in',
  output: app_id + '.metainfo.xml',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'metainfo')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util,
    args: ['validate', '--relax', appstream_file]
  )
endif

install_data(app_id + '.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0', 'schemas')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

# tessdata install_data removed here to avoid build failures when the file is not in the git repo.
# Tesseract model download and installation is handled by the Flatpak manifest instead.

subdir('icons')

blueprints = custom_target('blueprints',
  input: files(
    'ui/preferences_dialog.blp',
    'ui/preferences_general.blp',
    'ui/preferences_languages.blp',
    'ui/shortcuts.blp',
    'ui/window.blp',
    'ui/language_popover.blp',
    'ui/language_popover_row.blp',
    'ui/language_row.blp',
    'ui/welcome_page.blp',
    'ui/extracted_page.blp',
    'ui/share_row.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', meson.current_source_dir() / 'ui', '@INPUT@'],
)

app_resources = gnome.compile_resources(app_id,
    app_id + '.gresource.xml',
    gresource_bundle: true,
    dependencies: blueprints,
    source_dir: [meson.current_build_dir(), meson.current_source_dir()],
    install: true,
    install_dir: pkgdatadir
)
