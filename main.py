import argparse
import json
import os.path
import subprocess
import sys
import re
import time
import webbrowser

import requests
from bs4 import BeautifulSoup

already_searched = False


class Anime:
    episodes = dict()
    last_episode = ''

    def __init__(self, file_name):
        self.file_name = file_name
        try:
            with open(file_name, 'r') as file:
                self.anime_info = json.load(file)
                self.name = self.anime_info['name']
                self.link = self.anime_info['link']
                self.new_episode = False
                self.last_episode = self.anime_info['last_episode']
                self.last_search = self.anime_info['last_search']
                if time.localtime()[2] > self.last_search[0] or time.localtime()[1] > self.last_search[1]:
                    if not already_searched:
                        self.check_episodes()
                file.close()
        except json.decoder.JSONDecodeError:
            print(f"Erro: O arquivo {self.file_name} foi corrompido, por favor adicione o anime novamente.")
            os.remove(self.file_name)

    def check_episodes(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        soup = BeautifulSoup(requests.get(self.link, headers=headers).content, "html.parser")
        divs = soup.find('div', {"id": "episodio_box"}).find_all('a')

        try:
            with open(self.file_name, 'w') as file:
                try:
                    if len(divs) > self.anime_info['ep_num']:
                        self.new_episode = True
                except KeyError:
                    file.close()
                    return print(f'Erro ao checar por novos episódios de {self.name}')
                try:
                    self.anime_info['last_search'] = [time.localtime()[2], time.localtime()[1]]
                    self.anime_info["ep_num"] = len(divs)
                except KeyError:
                    self.anime_info.update({'last_search': [time.localtime()[2], time.localtime()[1]]})
                json.dump(self.anime_info, file, indent=4)
                file.close()
        except KeyError:
            return print(f'Erro ao checar por novos episódios de {self.name}')

        print(f'Checando por novos episódios de "{self.name}"...')

    def get_episodes(self, init=False):
        self.episodes.clear()
        headers = {'User-Agent': 'Mozilla/5.0'}
        soup = BeautifulSoup(requests.get(self.link, headers=headers).content, "html.parser")
        divs = soup.find('div', {"id": "episodio_box"}).find_all('a')
        for div in divs:
            url = div.get('href')
            aux = div.find('img').get('title')
            aux = aux[aux.find("Episódio") + 9:]
            try:
                while re.match(r'[^A-zÁ-ú]', aux[0]):
                    aux = aux[1:]
            except IndexError:
                pass
            ep_name = f'{len(self.episodes) + 1}. "{aux}"'
            if len(divs) >= 10:
                if len(self.episodes) + 1 <= 9:
                    ep_name = ' ' + ep_name
            self.episodes[ep_name] = url
        if not init:
            with open(self.file_name, 'w') as file:
                anime_info = {'name': self.name, 'link': self.link,
                              'last_episode': self.last_episode, 'ep_num': len(self.episodes),
                              'last_search': self.last_search}
                json.dump(anime_info, file, indent=4)
                file.close()
        return self.episodes

    def call(self, ep=None):
        headers = {'User-Agent': 'Mozilla/5.0'}
        if ep is None:
            return webbrowser.open(self.link)
        with open(self.file_name, 'w') as file:
            anime_info = {'name': self.name, 'link': self.link, 'last_episode': ep, 'ep_num': len(self.episodes),
                          'last_search': self.last_search}
            json.dump(anime_info, file, indent=4)
            url = list(self.episodes.values())[ep]
            soup = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")
            new_url = soup.find('div', {'id': 'Link'}).find('a').get('href')
            file.close()
        try:
            return subprocess.run(["google-chrome", f"--app={new_url}", "--class=WebApp-AnimesOrion4662",
                                   "--user-data-dir=/home/drumm-leo/.local/share/ice/profiles/AnimesOrion4662"])
        except FileNotFoundError:
            return webbrowser.open(new_url)


def add_anime(anime_name, anime_link):
    with open(os.path.join(os.path.expanduser("~"), f"Animes/{anime_name}.json"), 'w') as file:
        anime_info = {'name': anime_name, 'link': anime_link, 'last_episode': '', 'ep_num': 0, 'last_search':
                      [time.localtime()[2], time.localtime()[1]]}
        json.dump(anime_info, file, indent=4)
        file.close()


def remove_anime(anime_):
    try:
        os.remove(anime_.file_name)
        return True
    except OSError:
        print("Anime não encontrado. Por favor, tente novamente...")
        print(anime_.file_name)
        return False


def get_input(input_string, maximum=None, minimum=None, keys=None):
    try:
        if keys:
            answer = input(input_string)
            if answer.lower() in keys:
                return answer
            else:
                answer = int(answer)
        else:
            answer = int(input(input_string))
    except ValueError:
        print("Opção inválida!")
        return get_input(input_string, maximum, minimum, keys)
    else:
        if maximum is not None:
            if answer > maximum:
                print("Opção inválida!")
                return get_input(input_string, maximum, minimum, keys)
        if minimum is not None:
            if answer < minimum:
                print("Opção inválida!")
                return get_input(input_string, maximum, minimum, keys)
        if answer <= 0:
            print("Opção inválida!")
            return get_input(input_string, maximum, minimum, keys)
        return answer - 1


def test_link(input_string):
    headers = {'User-Agent': 'Mozilla/5.0'}
    link = input(input_string)
    try:
        r = requests.get(link, headers=headers)
    except requests.exceptions.MissingSchema:
        print("URL inválido, por favor tente novamente.")
        return test_link(input_string)
    if r.status_code == 200:
        return link
    print("Não é possível conectar a este URL, por favor cheque sua conexão com a internet e tente novamente.")
    return test_link(input_string)


def get_link_by_name(name):
    headers = {'User-Agent': 'Mozilla/5.0'}
    if os.path.isfile(os.path.join(os.path.expanduser("~"), "Animes/anime_dict.json")):
        with open(os.path.join(os.path.expanduser("~"), "Animes/anime_dict.json"), 'r') as file:
            anime_dict = json.load(file)
            if name.lower() in anime_dict.keys():
                return anime_dict[name.lower()]
            in_list = False
            for anime in anime_dict:
                if name.lower() in anime:
                    print(f'Você se refere a "{anime}"?')
                    in_list = True
            if in_list:
                new_name = input('Digite uma das sugestões acima ou deixe vazio ' +
                                 'para tentar encontrar um link pelo nome dado: ')
                if new_name.lower() in anime_dict.keys():
                    return get_link_by_name(new_name)
            file.close()
    else:
        download = requests.get('https://drive.google.com/u/0/uc?id=1Mg8mYSwiKQJ8PGYuip9gZJG55igY6MkH&export=download',
                                headers=headers)
        with open(os.path.join(os.path.expanduser("~"), "Animes/anime_dict.json"), 'wb') as file:
            file.write(download.content)
            file.close()
        return get_link_by_name(name)
    link = f"https://animesorionvip.com/animes/{'-'.join(name.lower().split())}/i"
    r = requests.get(link, headers=headers)
    if r.status_code == 200 and BeautifulSoup(r.content, "html.parser").find('div', {"id": "episodio_box"}):
        append_on_dict = get_input("Quer adicionar esse anime às sugestões da busca de animes? (s/n): ",
                                   0, 0, keys=['s', 'n'])
        if append_on_dict == 's':
            temp = dict()
            with open(os.path.join(os.path.expanduser("~"), "Animes/anime_dict.json"), 'r') as file:
                temp.update(json.load(file))
                file.close()
            temp.update({name.lower(): link})
            with open(os.path.join(os.path.expanduser("~"), "Animes/anime_dict.json"), 'w') as file:
                json.dump(temp, file, indent=4)
                file.close()
        return link
    return False


def main():
    anime_list = []
    directory = os.path.join(os.path.expanduser("~"), "Animes")
    if not os.path.isdir(directory):
        print("Bem-Vindo ao Animan!")
        name = input("Por favor, digite o nome do primeiro anime a ser incluído: ")
        os.mkdir(directory)
        link = get_link_by_name(name)
        if not link:
            print("Desculpe, não foi possível obter o link pelo nome dado...")
            get_link_manually = get_input("Gostaria de digitar o link manualmente? (s/n): ", 0, 0, ['s', 'n'])
            if get_link_manually == 's':
                link = test_link("Digite o link do anime: ")
            else:
                sys.exit()
        add_anime(name, link)
        print(f'Anime "{name}" adicionado com sucesso!\n')
        return main()
    else:
        for file in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, file)) and file != "anime_dict.json":
                anime = Anime(os.path.join(directory, file))
                anime_list.append(anime)

        parser = argparse.ArgumentParser()
        parser.add_argument("-a", type=int, nargs='+', help="Anime a ser executado", dest="anime")

        args = parser.parse_args()

        if args.anime:
            if len(args.anime) == 1:
                anime_name = anime_list[args.anime[0] - 3].name
                for anime in anime_list:
                    if anime.name == anime_name:
                        return anime.call()
                print("Erro: Nenhum anime registrado no número dado.")
            elif len(args.anime) == 2:
                try:
                    anime_list[args.anime[0] - 3].get_episodes()
                except IndexError:
                    return print("Erro: Nenhum anime registrado no número dado.")
                anime_name = anime_list[args.anime[0] - 3].name
                for anime in anime_list:
                    if anime.name == anime_name:
                        try:
                            return anime.call(args.anime[1] - 1)
                        except IndexError:
                            return print("Erro: Número de episódio inválido!")
                return print("Erro: Nenhum anime registrado no número dado.")
            else:
                return print(f"Erro: Esperado no máximo 2 argumentos mas {len(args.anime)} foram passados")

        global already_searched
        already_searched = True
        print()

        print('Escolha um anime:')
        anime_list.sort(key=lambda x: x.name)
        for n, anime in enumerate(anime_list):
            if anime.new_episode:
                print(f"{n + 1}. {anime.name}\t(Novo Episódio!)")
                anime.new_episode = False
            else:
                print(f"{n + 1}. {anime.name}")
        print('Digite "a" para adicionar um anime, "r" para remover ou "s" para sair do programa.')

        action = get_input("> ", len(anime_list), keys=["a", "r", "s"])

        print()

        if action == "a":
            name = input("Digite o nome do anime a ser incluído: ")
            link = get_link_by_name(name)
            if not link:
                print("Desculpe, não foi possível obter o link pelo nome dado...")
                get_link_manually = get_input("Gostaria de digitar o link manualmente? (s/n): ", 0, 0, ['s', 'n'])
                if get_link_manually == 's':
                    link = test_link("Digite o link do anime: ")
                else:
                    return main()
            add_anime(name, link)
            print(f'Anime "{name}" adicionado com sucesso!\n')
            anime_list.clear()
            return main()
        elif action == "r":
            while True:
                anime_num = get_input("Qual anime você quer remover?\n> ", len(anime_list), 1)
                anime = anime_list[anime_num]
                if remove_anime(anime):
                    print(f'Anime "{anime.name}" removido com sucesso!\n')
                    return main()
        elif action == "s":
            sys.exit()
        else:
            anime = anime_list[action]
            print(f'Episódios disponíveis para "{anime.name}":')
            anime.get_episodes()
            for episode in anime.episodes:
                if anime.last_episode != '':
                    if episode == list(anime.episodes.keys())[anime.last_episode]:
                        print(episode, "*")
                    else:
                        print(episode)
                else:
                    print(episode)
            print(f'Digite "*" para ir direto para o próximo episódio ou "s" para voltar ao menu principal.')
            action = get_input("\nSelecione um episódio da lista acima: ",
                               len(anime.episodes), keys=['*', 's'])
            if action == '*':
                if anime.last_episode in ['', len(anime.episodes) - 1]:
                    return anime.call(0)
                return anime.call(anime.last_episode + 1)
            if action == "s":
                print()
                anime.episodes.clear()
                return main()

            return anime.call(action)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo usuário.")
    except requests.exceptions.ConnectionError:
        print("Erro: Verifique sua a conexão com a internet!")
    except json.decoder.JSONDecodeError:
        print(f"Erro: Os arquivos do programa foram corrompidos, por favor delete o arquivo " +
              f"{os.path.join(os.path.expanduser('~'), 'Animes/anime_dict.json')} e tente novamente.")
