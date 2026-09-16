import os
import shutil
import subprocess
import sys
import time

QUEUE_FILENAME = 'voice_queue.jsonl'
POLL_INTERVAL_SECONDS = 0.5


def speak_name(name):
    greeting = f'Welcome, {name}'
    if sys.platform == 'win32':
        environment = os.environ.copy()
        environment['SNIFFER_SPEECH_NAME'] = greeting
        speech_command = (
            '$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
            '$voice.Speak($env:SNIFFER_SPEECH_NAME); '
            '$voice.Dispose()'
        )
        command = [
            'powershell',
            '-NoProfile',
            '-ExecutionPolicy',
            'Bypass',
            '-Command',
            speech_command,
        ]
        run_options = {'creationflags': subprocess.CREATE_NO_WINDOW}
    else:
        speech_engine = shutil.which('espeak')
        if speech_engine is None:
            return
        command = [speech_engine, greeting]
        run_options = {}

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        **run_options,
    )


def main():
    with open(QUEUE_FILENAME, 'a+', encoding='utf-8') as queue_file:
        queue_file.seek(0, os.SEEK_END)

        while True:
            line = queue_file.readline()
            if line:
                name = line.strip()
                if name:
                    speak_name(name)
            else:
                time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == '__main__':
    main()
