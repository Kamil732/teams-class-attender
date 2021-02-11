from cx_Freeze import setup, Executable

base = None

executables = [Executable("bot.py", base=base)]

packages = ['idna', 'codecs', 'os', 'chromedriver_autoinstaller',
            'sqlite3', 'time', 'selenium', 'schedule', 're', 'datetime']
options = {
    'build_exe': {
        'packages': packages,
    },
}

setup(
    name='Teams class attender BOT',
    options=options,
    version='0.1',
    description='Teams BOT',
    executables=executables
)
