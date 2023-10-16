import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import pyautogui

import json, re
import  keyboard
os.system("cls")

GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")

def click_element(xpath, driver, type=By.XPATH):
    WebDriverWait(driver, 99999999).until(EC.element_to_be_clickable((type, xpath))).click()

def login(email, password, driver):
    driver.get("https://chat.openai.com/")
    click_element('//div[text()="Log in"]', driver)
    click_element('//button[@data-provider="google"]', driver)

    email_field = WebDriverWait(driver, 99999999).until(EC.element_to_be_clickable((By.XPATH, '//input[@type="email"]')))
    email_field.send_keys(email)
    click_element('//span[text()="Next"]', driver)

    password_field = WebDriverWait(driver, 99999999).until(EC.element_to_be_clickable((By.XPATH, '//input[@type="password"]')))
    password_field.send_keys(password)
    click_element('//span[text()="Next"]', driver)

    time.sleep(4) 
    driver.get("https://chat.openai.com/?model=gpt-4")
    click_element('//div[text()="Okay, let’s go"]', driver)



def submit_prompt(prompt, driver):
    prompt_field = driver.find_element(By.ID, "prompt-textarea")
    driver.execute_script(f"arguments[0].value = `{prompt}`;", prompt_field) 
    prompt_field.send_keys(Keys.SPACE)  

    click_element('button[data-testid="send-button"]', driver, By.CSS_SELECTOR)
    print("clicked")
    time.sleep(1)
    regen_btn = (By.XPATH, "//div[contains(text(), 'Regenerate')]")
    WebDriverWait(driver, 99999999).until(EC.presence_of_element_located(regen_btn))
    print("regen found")

    code_elements = driver.find_elements(By.TAG_NAME, "code")
    answer = code_elements[-1].text.strip() if code_elements else None

    if not answer:
        answer_element = driver.find_element(By.CSS_SELECTOR, ".markdown.prose.w-full.break-words")
        answer = answer_element.text.strip()

    return answer

def upload_image(prompt, image_path, driver):
    print("Upload called")
    wait = WebDriverWait(driver, 99999999)
    upload = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]')))
    file_path = os.path.abspath(image_path)

    upload.send_keys(file_path)

    driver.execute_script("arguments[0].value = '';", upload)
    time.sleep(1)  
    return submit_prompt(prompt, driver)


def create_driver():
    options = uc.ChromeOptions()
    options.headless = False
    return uc.Chrome(options=options)


def extract_json(string):
    extracted = re.search(r'\{[^{}]*\}', string).group()
    if not extracted: return None
    return json.loads(extracted)

def main():
    driver = create_driver()
    login(GOOGLE_EMAIL, GOOGLE_PASSWORD, driver)

    prompt = f'''
You will be piloting a Windows 11 computer.
You have been given the ability to type keys and to click
The screen has a resolution of 1920x1080.

You will output your commands in the following format:

Wrap your commands in a JSON code block.

Do not write comments in your commands.

!EXAMPLES START!
{{
    "mouse": [
        {{
            "x_coordinate": 1,
            "y_coordinate": 1,
            "button_side": "left" || "right"
        }},
        {{
            "x_coordinate": 1,
            "y_coordinate": 1,
            "button_side": "left" || "right"
        }}
    ],
    "keyboard": [
        {{
            "special_keys": "ctrl+shift+space+enter",
            "words": "anything you put here will be typed"
        }},
        {{
            "special_keys": "ctrl+shift+space+enter",
            "words": "anything you put here will be typed"
        }}
    ]
}}
!EXAMPLES END!

If you do not want to use the mouse or keyboard, omit the key of the keyboard or mouse.
    
Reason out loud first, then append your commands to the end of your message.

ONLY ONCE YOU START RECIEVING IMAGES WILL YOU BE ALLOWED TO INPUT COMMANDS INTO THE COMPUTER.

YOUR TASK IS TO {input("Task for GPT-4: ")}
'''

    submit_prompt(prompt, driver)
    start_screenshotting(driver)


def handle_keyboard(keyboarddata):
    keys = keyboarddata.get('special_keys')
    words = keyboarddata.get('words')

    if words:
        for k in words:
            keyboard.press(k)
            time.sleep(0.1)
            keyboard.release(k)


    if keys and not keys == "":
        keyboard.press(keys)
        time.sleep(1)
        keyboard.release(keys)


def handle_mouse(mousedata):
    x = mousedata.get('x_coordinate')
    y = mousedata.get('y_coordinate')
    button_type = mousedata.get('button_side')

    pyautogui.moveTo(x, y)
    pyautogui.click(button=button_type)
    print("clicked the mouse", x,y, button_type)


def start_screenshotting(driver):
    amount_of_screenshots = 1 
    while True:
        myScreenshot = pyautogui.screenshot()
        image_name = f"screen{amount_of_screenshots}.png"
        myScreenshot.save(image_name)

        output = upload_image(f'Screenshot {amount_of_screenshots}', image_name, driver)
        amount_of_screenshots += 1 

        print(output)

        output = output.replace("(", "{")
        output = output.replace(")", "}")

        output = json.loads(output)
        print(output)
        mouse = output.get('mouse')
        keyboard = output.get('keyboard')

        if mouse:
            for mousedata in mouse:
                handle_mouse(mousedata)


        if keyboard:
            for keyboarddata in keyboard:
                handle_keyboard(keyboarddata)

        time.sleep(5)
main()

def test():
    driver = create_driver()
    driver.maximize_window()
    login(GOOGLE_EMAIL, GOOGLE_PASSWORD, driver)
    submit_prompt("hello", driver)

    upload_image("what this", "screen1.png", driver)
    upload_image("what this", "screen2.png", driver)

#test()
