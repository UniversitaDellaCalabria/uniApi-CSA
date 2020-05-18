from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='uniApiCSA',
      version='0.3',
      description="Custom interface to Cineca CSA API",
      long_description=readme(),
      classifiers=['Development Status :: 5 - Production/Stable',
                   'License :: OSI Approved :: BSD License',
                   'Programming Language :: Python :: 3'],
      url='https://github.com/UniversitaDellaCalabria/uniApi-CSA',
      author='Giuseppe De Marco',
      author_email='giuseppe.demarco@unical.it',
      license='BSD',
      scripts=['csa_api/csa_api.py'],
      packages=['csa_api'],
      install_requires=[
                      'requests'
                  ],
     )
