project('anura',
          version: '0.1.4',
    meson_version: '>= 1.5.0',
  default_options: [ 
    'warning_level=2',
    'werror=false', # Do not treat compiler warnings as fatal errors
  ],
)

author = 'd3msudo'
domain = 'com.github'
app_id = '@0@.@1@.@2@'.format(domain, author, meson.project_name())
gitrepo = 'https://github.com/@0@/@1@'.format(author, meson.project_name())
website = 'https://github.com/d3msudo/anura'

i18n = import('i18n')
pymod = import('python')
python = pymod.find_installation('python3')
gnome = import('gnome')

prefix = get_option('prefix') 
bindir = get_option('bindir') 
datadir = get_option('datadir') 

pkgdatadir = prefix / datadir / meson.project_name()
pythondir = python.get_install_dir() / 'anura'
localedir = prefix / get_option('localedir')

# Generate _release_notes.py from CHANGELOG.md
release_notes_py = custom_target('release_notes',
  input: 'CHANGELOG.md',
  output: '_release_notes.py',
  command: [
    python,
    meson.project_source_root() / 'build-aux' / 'generate_release_notes.py',
    '@INPUT@',
    '@OUTPUT@',
    meson.project_version()
  ],
  install: true,
  install_dir: pythondir
)

install_subdir('anura', install_dir: python.get_install_dir())

subdir('data')
subdir('bin')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')
