from distutils.core import setup
setup(
  name = 'bhpy',
  packages = ['bhpy'],
  version = '2.1.0',
  license='MIT License',
  description = "Python bindings to use Becker & Hickls' hardware control dll and API",
  author = 'Marscheck',
  author_email = 'marscheck@becker-hickl.de',
  url = 'https://www.becker-hickl.com/',
  download_url = 'https://git.becker-hickl.com/products/bhpy/-/archive/v2.1.0/bhpy-v2.1.0.tar.gz',
  keywords = ['FLIM', 'Fluorescence lifetime', 'TCSPC', 'photon counting', 'BH', 'Becker&Hickl', 'molecular imaging', 'SPC', 'SPCM'],
  install_requires=[
    'numpy>=1.24.2,<2',
    'appdirs>=1.4.4,<2'
  ],
  classifiers=[
    'Development Status :: 5 - Production/Stable', # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Science/Research',
    'Intended Audience :: Developers',
    'Intended Audience :: Healthcare Industry',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development :: Libraries',
    'Topic :: System :: Hardware :: Hardware Drivers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Operating System :: OS Independent',
  ],
  include_package_data = True,
  package_data={"bhpy": ['ControlQC008.dll']},
)