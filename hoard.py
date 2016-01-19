import requests
import os
from sys import argv, exit
from time import sleep
from bs4 import BeautifulSoup
from colorama import Fore, Style, init


# colorama init.
init(autoreset=True)


def parse_html(soup):
        #  parse the html doc for all javascript and css dependencies
    resources = {}

    js_resources = soup.findAll('script', {"src": True})
    css_resources = soup.findAll('link', {"href": True})

    resources["js"] = []
    for source in js_resources:
        resources["js"].append(source['src'])

    resources["css"] = []
    for source in css_resources:
        resources["css"].append(source['href'])

    return resources


def build_new_html(target_html_file, soup, resources_directory):
        # build new html with the local paths included

    for source in soup.findAll('script', {"src": True}):
        if "//" in source['src']:
            local_filename = source['src'].split('/')[-1]
            source['src'] = os.path.join(resources_directory, "js", local_filename)

    for source in soup.findAll('link', {"href": True}):
        if "//" in source['href']:
            local_filename = source['href'].split('/')[-1]
            source['href'] = os.path.join(resources_directory, "css", local_filename)

    filename, file_extension = os.path.splitext(target_html_file)
    target_html_file = filename + "_modified" + file_extension

    with open(target_html_file, "wb") as new_file:
        new_file.write(str(soup.prettify()))

    message("::Modified file written to {}".format(
        target_html_file), 3, 'success')


def resources_handler(resources, target_local_directory):
    # download and organize dependencies


    if len(resources['css']) < 1 and len(resources['js']) < 1:
        #  html docs with missing script srcs and or link hrefs along with
        #  malformed content should trigger this condition.
        message("No resources were found in the target html file..", 3, 'warning')
        exit()

    css_save_location = os.path.join(target_local_directory, 'css')
    js_save_location = os.path.join(target_local_directory, 'js')

    if not os.path.exists(target_local_directory):
        create_target_directory = ""

        while create_target_directory.lower() not in ('y', 'yes', 'n', 'no'):
            create_target_directory = raw_input(Fore.CYAN + "The target local directory"
                                                "does not exists, would you like "
                                                "to create it? [y/N] ")

        if create_target_directory in ('y', 'yes'):
            os.mkdir(target_local_directory)

        elif create_target_directory in ('n', 'no'):
            message("Well then, not much left but the end of the road... ", 5, 'warning')
            message("Bye now.", 1)
            exit(1)



    #  create the targetpath/css and targetpath/js
    #  directories if they do not exist already.
    if not os.path.exists(css_save_location):
        os.mkdir(css_save_location)

    if not os.path.exists(js_save_location):
        os.mkdir(js_save_location)

    # download all of the remote dependencies to local
    for resource in resources["css"]:
        if "//" in resource:
            if "http" not in resource:
                # In case '//' is used without '`protocol`:' in the html doc.
                resource = "https:" + resource
            download_file(resource, css_save_location)

    for resource in resources["js"]:
        if "//" in resource:
            if "http" not in resource:
                resource = "https:" + resource
            download_file(resource, js_save_location)


def download_file(url, local_directory):
    local_filename = url.split('/')[-1]
    save_directory = os.path.join(local_directory, local_filename)

    try:
        r = requests.get(url, stream=True)
        with open(save_directory, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        message("{} ====> {}.".format(url, save_directory), 0, 'success')
        return local_filename

    except requests.exceptions.RequestException as e:
        message("{} ====> {}.".format(url, save_directory), 0, 'error')
        return None


def message(text, delay, status=None):
    if status == 'success':
        print(Fore.GREEN + text)
    elif status == 'warning':
        print(Fore.YELLOW + text)
    elif status == 'error':
        print(Fore.RED + text)
    else:
        print(text)

    sleep(delay)


if __name__ == "__main__":
    try:
        target_html_file = argv[1]
        target_resources_directory = argv[2]

        with open(target_html_file, "r") as html_file:
            soup = BeautifulSoup(html_file, 'lxml')

        resources = parse_html(soup)
        resources_handler(resources, target_resources_directory)
        build_new_html(target_html_file, soup, target_resources_directory)

    except IndexError:
        message("Yikes, did you specify both of the required arguments?", 1, 'warning')
        message("Usage: python hoard.py target.html resources_save_to_directory", 2)
        exit()
