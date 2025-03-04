from setuptools import setup

with open('README.md', 'r', encoding='utf-8') as fp:
    readme = fp.read()

with open('scapi/others/common.py', 'r', encoding='utf-8') as fp:
    init = fp.read()

with open('requirements.txt', 'r', encoding='utf-8') as fp:
    requirements = fp.readlines()

var = init.replace(" ","").split("__version__=\"")[1].split("\"")[0]

setup(
    name="scapi",
    version=var,
    description="ScratchAttachより高機能をめざして。",
    long_description=readme,
    long_description_content_type='text/markdown',
    author="kakeruzoku",
    author_email="kakeruzoku@gmail.com",
    maintainer="kakeruzoku",
    maintainer_email="kakeruzoku@gmail.com",
    url="https://github.com/kakeruzoku/scapi",
    download_url="https://github.com/kakeruzoku/scapi",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    license="MIT",
    keywords=['scratch api', 'scapi', 'scratch api python', 'scratch python', 'scratch for python', 'scratch', 'scratch bot','scratch tools','scratchapi'],
    install_requires=requirements,
    include_dirs=["scapi", "scapi.*"],
)
