"""
Fast input helper for Dota 2 Automaton Attack.

The minigame currently does not penalize incorrect letters, so repeatedly sending
the alphabet advances whichever word is active without OCR latency.

F8  - start/stop
F9  - emergency stop
F10 - stop and exit
"""

from __future__ import annotations

import argparse
import threading
import time

import pydirectinput
from pynput import keyboard


KEY_CYCLE = "abcdefghijklmnopqrstuvwxyz"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fast input helper for Automaton Attack")
    parser.add_argument(
        "--interval",
        type=float,
        default=0.001,
        help="pause between keys in seconds (default: 0.001)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60,
        help="automatic safety stop in seconds (default: 60)",
    )
    return parser.parse_args()


class AlphabetCycler:
    def __init__(self, interval: float, timeout: float) -> None:
        self.interval = max(0.0, interval)
        self.timeout = max(1.0, timeout)
        self.running = threading.Event()
        self.exiting = threading.Event()
        self.worker: threading.Thread | None = None

    def toggle(self) -> None:
        if self.running.is_set():
            self.stop()
        else:
            self.start()

    def start(self) -> None:
        if self.running.is_set():
            return
        self.running.set()
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()
        print("[INPUT] Started. Press F8 or F9 to stop.")

    def stop(self) -> None:
        if self.running.is_set():
            self.running.clear()
            print("[INPUT] Stopped.")

    def close(self) -> None:
        self.stop()
        self.exiting.set()

    def _run(self) -> None:
        started = time.monotonic()
        while self.running.is_set() and not self.exiting.is_set():
            for letter in KEY_CYCLE:
                if not self.running.is_set() or self.exiting.is_set():
                    return
                pydirectinput.press(letter)
                if self.interval:
                    time.sleep(self.interval)
            if time.monotonic() - started >= self.timeout:
                self.running.clear()
                print(f"[INPUT] Safety timeout reached ({self.timeout:g}s).")
                return


def main() -> None:
    args = parse_args()
    pydirectinput.PAUSE = 0
    cycler = AlphabetCycler(args.interval, args.timeout)

    print("Ready: F8 = start/stop, F9 = emergency stop, F10 = exit")
    print("Keep Dota 2 focused before starting.")

    def on_press(key: keyboard.Key | keyboard.KeyCode):
        if key == keyboard.Key.f8:
            cycler.toggle()
        elif key == keyboard.Key.f9:
            cycler.stop()
        elif key == keyboard.Key.f10:
            cycler.close()
            print("Exited.")
            return False
        return None

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    main()
