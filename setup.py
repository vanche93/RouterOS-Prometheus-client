try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_long_description():
    with open('README.md') as readme_file:
        return readme_file.read()


setup(
    name='RouterOS-Prometheus-client',
    version='0.0.4',
    license='MIT',
    url='https://github.com/vanche93/RouterOS-Prometheus-client',
    author='Ivan Burashev',
    author_email='vanche93@yandex.ru',
    description='Python Prometheus client to RouterBoard devices produced by MikroTik.',
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=['routeros_prometheus_client'],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.6',
    install_requires=['RouterOS-api', 'prometheus_client'],
    entry_points={
        'console_scripts': [
            'routeros-prometheus-client = routeros_prometheus_client.__main__:main',
        ]
    },
)
