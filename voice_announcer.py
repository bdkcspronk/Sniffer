import os
import subprocess
import time

QUEUE_FILENAME = 'voice_queue.jsonl'
POLL_INTERVAL_SECONDS = 0.5


def speak_name(name):
    greeting = f'Welcome, {name}'
    environment = os.environ.copy()
    environment['SNIFFER_SPEECH_NAME'] = greeting
    speech_command = (
        '$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
        '$voice.Speak($env:SNIFFER_SPEECH_NAME); '
        '$voice.Dispose()'
    )

    subprocess.run(
        [
            'powershell',
            '-NoProfile',
            '-ExecutionPolicy',
            'Bypass',
            '-Command',
            speech_command,
        ],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
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
