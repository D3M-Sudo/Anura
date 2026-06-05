python_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'config.py',
]

velis_dir = APP_ID.split('.')[-1]
install_data(python_sources, install_dir: py_installation.get_install_dir() / velis_dir)

subdir('core')
subdir('models')
subdir('services')
subdir('utils')
subdir('widgets')
