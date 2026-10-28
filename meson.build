project('anura',
          version: '0.2.1',
    meson_version: '>= 1.5.0',
  default_options: [ 
    'warning_level=2',
    'werror=false', # Do not treat compiler warnings as fatal errors
  ],
)

author = 'd3msudo'
github_owner = 'D3M-Sudo'
github_repo = 'Anura'
domain = 'io.github'
app_id = '@0@.@1@.@2@'.format(domain, author, meson.project_name())
gitrepo = 'https://github.com/@0@/@1@'.format(github_owner, github_repo)
website = gitrepo

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

# Application license: Flathub expects the app's own license text in the
# bundle. Installing it from Meson keeps it independent of flatpak-builder's
# automatic source-license recording (#478, #493).
install_data('LICENSE',
  install_dir: join_paths(datadir, 'licenses', app_id)
)

# Generate _release_notes.py from CHANGELOG.md
release_notes_py = custom_target('release_notes',
  input: ['CHANGELOG.md', 'build-aux/generate_release_notes.py'],
  output: '_release_notes.py',
  command: [
    python,
    '@INPUT1@',
    '@INPUT0@',
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
