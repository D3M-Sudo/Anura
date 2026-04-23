# bin/meson.build
#
# Configuration and installation for the Anura executable entry point.
# This script handles the variable substitution within 'anura.in'.

# 1. Configuration Data Setup
# All variables defined here will replace the @VARIABLE@ placeholders in anura.in
conf = configuration_data()

# Project metadata (inherited from root meson.build)
conf.set('VERSION', meson.project_version())
conf.set('projectname', meson.project_name())

# Explicit Application ID - Must match the GSettings schema and GResource name
# Standard: com.github.d3msudo.anura
conf.set('appid', 'com.github.d3msudo.anura')

# Path configurations for system stability
# Ensure localization and package data are correctly mapped
conf.set('prefix', prefix)
conf.set('localedir', join_paths(prefix, get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

# Python environment setup
# Uses the full path of the detected python installation to avoid env conflicts
conf.set('PYTHON', python.full_path())
conf.set('pythondir', join_paths(prefix, pythondir))

# 2. Executable Generation
# Transform 'anura.in' (source) into 'anura' (executable script)
configure_file(
  input: meson.project_name() + '.in',
  output: meson.project_name(),
  configuration: conf,
  install_dir: bindir,
  # Security: Set explicit execute permissions (rwxr-xr-x)
  install_mode: 'rwxr-xr-x'
)

# 3. Development/Stability Target
# Allows testing the application without a full system install:
# Command: 'ninja -C build run'
myprogram = join_paths(meson.project_build_root(), 'bin', meson.project_name())
run_target('run',
  command: [myprogram]
)