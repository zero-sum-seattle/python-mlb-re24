from setuptools import find_packages, setup
setup(
    name='advpmsastats',
    packages=find_packages(include=['advpmsastats']),
    version='0.0.1',
    description="Advanced stats library Utilizing the Python-mlb-stats-api Python Wrapper for the MLB's Official Stats API",
    author='Kristian Nilssen',
    license='MIT',
    install_requires=[],
    setup_requires=['pytest'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)