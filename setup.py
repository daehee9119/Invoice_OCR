import io
from setuptools import find_packages, setup

setup(name             = 'Invoice_OCR',

      version          = '0.1',

      description      = 'Extract text from invoice image files',

      author           ='daehee.kim',

      author_email     ='daehee9119@gmail.com',

      url              = 'https://github.com/daehee9119/Invoice_OCR',

      install_requires = [
            'google-cloud-vision >= 1.0.0',
            'pdf2image >= 1.13.1'
      ],

      packages         = find_packages(exclude=[]),

      long_description = open('README.md').read(),

      python_requires  = '>=3.8',

      zip_safe         = False,

      )
