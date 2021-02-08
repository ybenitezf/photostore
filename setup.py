"""
Photostore
----------

Photo archive for adelante.cu
"""
from setuptools import find_packages, setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='photostore',
    version='0.0.9',
    url='https://github.com/ybenitezf/photostore',
    license='GPL',
    author='Yoel Benítez Fonseca',
    author_email='ybenitezf@gmail.com',
    description='Photo archive for adelante.cu',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    long_description=read('README.md'),
    platforms='any',
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov'],
    install_requires=[
        'Flask',
        'Flask-Migrate',
        'Flask-SQLAlchemy',
        'Flask-Login',
        'Flask-WTF',
        'flask-ldap3-login',
        'Flask-Breadcrumbs',
        'Flask-Menu',
        'Flask-Principal',
        'Flask-Caching',
        'Flask-Static-Digest',
        'Flask-Diced',
        'email-validator',
        'PyMySQL',
        'python-dotenv',
        'webpreview',
        'redis',
        'cryptography',
        'Pillow',
        'IPTCInfo3',
        'apifairy',
        'marshmallow-sqlalchemy',
        'celery',
        'Whoosh',
        'python-slugify',
        'adelacommon @ https://github.com/ybenitezf/adela-common/releases/download/v0.0.3/adelacommon-0.0.3-py3-none-any.whl'
    ],
    classifiers=[
        'Environment :: Web Environment', 
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent', 
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Multimedia :: Graphics :: Viewers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
    ]
)
