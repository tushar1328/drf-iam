from setuptools import setup, find_packages

setup(
    name='drf-iam',
    version='0.2.2',
    packages=find_packages(),  # Automatically finds all sub-packages
    include_package_data=True,  # Include non-Python files from MANIFEST.in
    install_requires=[
        'Django>=3.2',
        'djangorestframework>=3.12'
    ],
    author='Tushar Patel',
    author_email='tushar.patel@gmail.com',
    description='IAM-style roles and permissions for Django Rest Framework',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',  # Important if using Markdown
    url='https://github.com/tushar1328/drf-iam.git',  # Optional but helpful
    project_urls={
        'Documentation': 'https://drf-iam.readthedocs.io/en/latest/installation.html',
        'Source': 'https://github.com/tushar1328/drf-iam.git',
    },
    classifiers=[
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Or your license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Or your minimum supported Python version
)
