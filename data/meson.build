# Application ID definition
# Rigor: Explicitly using the new namespace for Anura
app_id = 'com.github.d3msudo.anura'

# Desktop File Integration
desktop_file = i18n.merge_file(
  input: app_id + '.desktop.in',
  output: app_id + '.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

# Desktop File Validation
desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file]
  )
endif

# AppStream Metadata (Required for Flathub/Software Manager)
appstream_file = i18n.merge_file(
  input: app_id + '.appdata.xml.in',
  output: app_id + '.appdata.xml',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'metainfo') # Modern path is 'metainfo'
)

# AppStream Validation
appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util,
    args: ['validate', appstream_file]
  )
endif

# GSettings Schema Installation
install_data(app_id + '.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0', 'schemas')
)

# Compile Schemas Validation
compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

# Default tesseract trained model
install_data('tessdata/eng.traineddata',
  install_dir: join_paths(get_option('datadir'), meson.project_name(), 'tessdata')
)

subdir('icons')

# UI Blueprints Batch Compilation
# Optimized path resolution to avoid blueprint-compiler sync issues
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
  command: [
    find_program('blueprint-compiler'), 
    'batch-compile', 
    '@OUTPUT@', 
    meson.current_source_dir() / 'ui', 
    '@INPUT@'
  ],
)

# GResource Compilation
app_resources = gnome.compile_resources(app_id,
    app_id + '.gresource.xml',
    gresource_bundle: true,
    dependencies: blueprints,
    source_dir: [meson.current_build_dir(), meson.current_source_dir()],
    install: true,
    install_dir: pkgdatadir
)
