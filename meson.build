project('anura',
          version: '0.1.0',
    meson_version: '>= 1.5.0',
  default_options: [ 'warning_level=2' ],
)

# Updated metadata for the Anura
author = 'd3msudo'
domain = 'com.github'
app_id = '@0@.@1@.@2@'.format(domain, author, meson.project_name())
gitrepo = 'https://github.com/@0@/@1@'.format(author, meson.project_name())
website = 'https://github.com/d3msudo/anura'

i18n = import('i18n')
pymod = import('python')
python = pymod.find_installation('python3')
gnome = import('gnome')

# Standard paths
prefix = get_option('prefix') 
bindir = get_option('bindir') 
datadir = get_option('datadir') 

# Important: pkgdatadir must match the directory where resources are stored
pkgdatadir = prefix / datadir / meson.project_name()
# Fix: Ensure python files are installed in a project-specific subdirectory
pythondir = python.get_install_dir() / 'anura'
localedir = prefix / get_option('localedir')

# Installation logic
# We install the package source as a subdirectory
install_subdir('anura', install_dir: python.get_install_dir())

# Recurse into subdirectories
subdir('bin')
subdir('data')
subdir('po')

# Post-installation script for icon cache, schemas, and desktop database
# Safety check: avoid errors if the script is missing during build-only CI
meson.add_install_script('build-aux/meson/postinstall.py')