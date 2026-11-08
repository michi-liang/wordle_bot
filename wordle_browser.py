import time
import argparse
from urllib.parse import urlencode
from wordle import load_words, filter_candidates
from wordle_bot_starter import my_guess

BASE_URL = 'http://127.0.0.1:8000/'


import platform
from pathlib import Path
from shutil import which


def create_driver(browser="chrome", headless=False):
    from selenium import webdriver

    browser = browser.lower()

    if browser == "chrome":
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)

    elif browser == "edge":
        options = webdriver.EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
        driver = webdriver.Edge(options=options)

    elif browser == "firefox":
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("-headless")
        driver = webdriver.Firefox(options=options)

    elif browser == "safari":
        if platform.system() != "Darwin":
            raise RuntimeError("Safari requires macOS.")
        if headless:
            raise RuntimeError("Safari does not support headless mode.")
        driver = webdriver.Safari()

    elif browser == "brave":
        options = webdriver.ChromeOptions()

        system = platform.system()
        if system == "Windows":
            paths = [
                Path.home() / "AppData/Local/BraveSoftware/Brave-Browser/Application/brave.exe",
                Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"),
                Path("C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"),
            ]
        elif system == "Darwin":
            paths = [
                Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser")
            ]
        else:
            paths = [
                Path(which("brave-browser") or ""),
                Path(which("brave") or ""),
            ]

        brave_path = next((p for p in paths if p.is_file()), None)
        if brave_path is None:
            raise RuntimeError("Brave browser not found.")

        options.binary_location = str(brave_path)
        if headless:
            options.add_argument("--headless=new")

        driver = webdriver.Chrome(options=options)

    else:
        raise ValueError(f"Unsupported browser: {browser}")

    driver.set_window_size(960, 900)
    return driver


def run_browser(answer='crane', choose_guess=my_guess,
                headless=False, browser='chrome'):
    # Lazy imports let the pure-Python solver/tests work without Selenium installed.
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait

    words = load_words()
    if answer not in words:
        raise ValueError('Choose an answer from words.txt')
    allowed = set(words)
    driver = create_driver(browser, headless)
    candidates, used, history = words[:], [], []
    try:
        driver.get(BASE_URL + '?' + urlencode({'answer': answer}))
        if driver.title != '15-112 Local Wordle':
            raise RuntimeError('Wrong page. Start local_server.py first.')
        for turn in range(6):
            guess = choose_guess(candidates[:], used[:])
            if guess not in allowed or guess in used:
                raise ValueError(f'Solver produced invalid/repeated guess: {guess}')
            field = driver.find_element(By.ID, 'guess-input')
            field.send_keys(guess)
            field.send_keys(Keys.ENTER)
            selector = '#history .result'
            WebDriverWait(driver, 5).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, selector)) == turn + 1)
            result = driver.find_elements(By.CSS_SELECTOR, selector)[-1]
            observed_guess = result.get_attribute('data-guess')
            pattern = result.get_attribute('data-pattern')
            if observed_guess != guess or len(pattern) != 5:
                raise RuntimeError('Unexpected browser feedback')
            used.append(guess)
            candidates = filter_candidates(candidates, guess, pattern)
            history.append((guess, pattern, len(candidates)))
            print(f'{turn+1}. {guess.upper()}  {pattern}  {len(candidates)} candidate(s)')
            if pattern == 'GGGGG':
                print('Solved in the browser!')
                return True, history
            time.sleep(2)
        print('Not solved within six guesses.')
        return False, history
    finally:
        if not headless:
            input("Press Enter to close the browser...")
        driver.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--answer', default='crane')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument(
        '--browser',
        choices=['chrome', 'edge', 'firefox', 'safari', 'brave'],
        default='chrome'
    )
    args = parser.parse_args()

    run_browser(
        args.answer,
        headless=args.headless,
        browser=args.browser
    )