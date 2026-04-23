project('anura',
          version: '1.6.0',
    meson_version: '>= 1.5.0',
  default_options: [ 'warning_level=2' ],
)

# Updated metadata for the Anura fork
author = 'd3msudo'
domain = 'com.github'
app_id = domain + '.' + author + '.' + meson.project_name()
gitrepo = 'https://github.com/' + author + '/' + meson.project_name()
website = 'https://github.com/d3msudo/anura'

i18n = import('i18n')
pymod = import('python')
python = pymod.find_installation()
gnome = import('gnome')

# Standard paths for Linux Mint / Cinnamon
prefix = get_option('prefix') 
bindir = get_option('bindir') 
datadir = get_option('datadir') 

# Important: pkgdatadir must match the directory where resources are stored
pkgdatadir = join_paths(prefix, datadir, meson.project_name())
pythondir = python.get_install_dir()
localedir = join_paths(prefix, get_option('localedir'))

# Installation logic
install_subdir('anura', install_dir: pythondir)

# Recurse into subdirectories
subdir('bin')
subdir('data')
subdir('po')

# Post-installation script for icon cache, schemas, and desktop database
meson.add_install_script('build-aux/meson/postinstall.py')
