project('velis',
  version: '0.1.0',
  meson_version: '>= 0.62.0',
  default_options: [ 'warning_level=2' ],
)

i18n = import('i18n')
gnome = import('gnome')

APP_ID = 'io.github.d3msudo.velis'

python = import('python')
py_installation = python.find_installation('python3')

subdir('data')
subdir('velis')
subdir('po')

gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
