from setuptools import setup, find_packages

setup(
    name="gpt_sql_assistant",
    version="0.1.0", 
    packages=find_packages(),
    install_requires=[  # List of external dependencies
        "openai>=1.0.0",
        "pandas>=1.0.0",
    ],
    entry_points={
        'console_scripts': [
            'gpt-sql-assistant = gpt_sql_assistant.main:main',
        ],
    },
    include_package_data=True,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',  # Use markdown for the README
    author="Your Name",
    author_email="your.email@example.com",
    description="A GPT-powered SQL assistant",
    url="https://github.com/sigma31/ec530-gpt-sql-application",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
