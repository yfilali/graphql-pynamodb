from setuptools import find_packages, setup

setup(
    name='graphene-pynamodb',
    version='0.3.1',

    description='Graphene PynamoDB integration',
    long_description=open('README.rst').read(),

    url='https://github.com/yfilali/graphql-pynamodb',

    author='Yacine Filali',
    author_email='yfilali@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],

    keywords='api graphql protocol rest relay graphene pynamodb dynamodb',

    packages=find_packages(exclude=['tests']),

    install_requires=[
        'six>=1.10.0',
        'graphene>=1.0',
        'pynamodb>=1.5.0',
        'singledispatch>=3.4.0.3',
        'wrapt>=1.10.8'
    ],
    setup_requires=['pytest-runner'],
    tests_require=[
        'pytest>=2.7.2',
        'mock'
    ],
    test_suite="graphene_pynamodb.tests",

)
