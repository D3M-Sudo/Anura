# data/ui/meson.build
# Note: We use .ui files directly as blueprint-compiler is not always available
# and we have pre-converted them for the initial commit.

compile_resources = gnome.compile_resources(
  'velis-resources',
  APP_ID + '.gresource.xml',
  source_dir: '.',
  c_name: 'velis',
)
