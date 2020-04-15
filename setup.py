try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def get_long_description():
    with open('README.md') as readme_file:
        return readme_file.read()

config = {
    'description': 'Python Prometheus client to RouterBoard devices produced by MikroTik.',
    'long_description': get_long_description(),
    'author': 'Ivan Burashev',
    'url': 'https://github.com/vanche93/routeros-prometheus-client',
    'author_email': 'vanche93@yandex.ru',
    'version': '0.1.0',
    'license': 'MIT',
    'install_requires': ['RouterOS-api', 'prometheus_client'],
    'packages': ['routeros_prometheus_client'],
    'name': 'RouterOS-Prometheus-client',
    'entry_points': {
        'console_scripts': [
            'routeros-prometheus-client = routeros_prometheus_client.__main__:main',
        ]
    },
    'classifiers': [
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    'python_requires': '>=3.6',
}

setup(**config)
