import argparse
import json
import sys
import time
import webbrowser
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ANIMES_DIR = Path.home() / "Animes"
ANIME_DICT_FILE = ANIMES_DIR / "anime_dict.json"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}


def today():
    t = time.localtime()
    return [t.tm_mday, t.tm_mon]


class Anime:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.episodes: dict = {}
        self.season_breaks: dict = {}
        self.new_episode = False
        with open(file_path, 'r') as f:
            self.info = json.load(f)
        self.name = self.info['name']
        self.link = self.info['link']
        self.last_episode = self.info['last_episode']
        self.last_search = self.info['last_search']

    def needs_check(self) -> bool:
        t = today()
        return t[0] > self.last_search[0] or t[1] > self.last_search[1]

    def check_episodes(self):
        print(f'Checando por novos episódios de "{self.name}"...')
        soup = BeautifulSoup(requests.get(self.link, headers=HEADERS).content, "html.parser")
        divs = soup.select('ul.episodios li a')
        try:
            if len(divs) > self.info['ep_num']:
                self.new_episode = True
            self.info['last_search'] = today()
            self.info['ep_num'] = len(divs)
        except KeyError:
            print(f'Erro ao checar por novos episódios de {self.name}')
            return
        with open(self.file_path, 'w') as f:
            json.dump(self.info, f, indent=4)

    def get_episodes(self, init=False) -> dict:
        self.episodes.clear()
        self.season_breaks.clear()
        soup = BeautifulSoup(requests.get(self.link, headers=HEADERS).content, "html.parser")

        seen_urls: set = set()
        collected = []
        season_num = 0

        for ul in soup.select('ul.episodios'):
            new_in_season = []
            for a in ul.select('li a'):
                url = a.get('href')
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                span = a.find('span', class_='episodiotitle')
                title = span.text.strip() if span else ''
                new_in_season.append((season_num + 1, title, url))
            if new_in_season:
                season_num += 1
                collected.extend(new_in_season)

        total = len(collected)
        prev_season = None
        for i, (snum, title, url) in enumerate(collected):
            ep_title = title or f"Episódio {i + 1}"
            ep_name = f'{i + 1}. "{ep_title}"'
            if total >= 10 and i < 9:
                ep_name = ' ' + ep_name
            if snum != prev_season:
                self.season_breaks[i] = snum
                prev_season = snum
            self.episodes[ep_name] = url

        if not init:
            with open(self.file_path, 'w') as f:
                json.dump({
                    'name': self.name, 'link': self.link,
                    'last_episode': self.last_episode,
                    'ep_num': total, 'last_search': self.last_search,
                }, f, indent=4)
        return self.episodes

    def call(self, ep=None):
        if ep is None:
            return webbrowser.open(self.link)
        with open(self.file_path, 'w') as f:
            json.dump({
                'name': self.name, 'link': self.link,
                'last_episode': ep, 'ep_num': len(self.episodes),
                'last_search': self.last_search,
            }, f, indent=4)
        return webbrowser.open(list(self.episodes.values())[ep])


def add_anime(name: str, link: str):
    with open(ANIMES_DIR / f"{name}.json", 'w') as f:
        json.dump({
            'name': name, 'link': link, 'last_episode': '',
            'ep_num': 0, 'last_search': today(),
        }, f, indent=4)


def remove_anime(anime: Anime) -> bool:
    try:
        anime.file_path.unlink()
        return True
    except OSError:
        print(f"Anime não encontrado: {anime.file_path}")
        return False


def get_input(prompt: str, maximum=None, minimum=None, keys=None):
    while True:
        raw = input(prompt)
        if keys and raw.lower() in keys:
            return raw.lower()
        try:
            answer = int(raw)
        except ValueError:
            print("Opção inválida!")
            continue
        if answer <= 0 or (maximum is not None and answer > maximum) or (minimum is not None and answer < minimum):
            print("Opção inválida!")
            continue
        return answer - 1


def test_link(prompt: str) -> str:
    while True:
        link = input(prompt)
        try:
            r = requests.get(link, headers=HEADERS)
        except requests.exceptions.MissingSchema:
            print("URL inválido, por favor tente novamente.")
            continue
        if r.status_code == 200:
            return link
        print("Não é possível conectar a este URL, por favor cheque sua conexão com a internet e tente novamente.")


def get_link_by_name(name: str):
    while True:
        if ANIME_DICT_FILE.is_file():
            with open(ANIME_DICT_FILE, 'r') as f:
                anime_dict = json.load(f)
            key = name.lower()
            if key in anime_dict:
                return anime_dict[key]
            suggestions = [k for k in anime_dict if key in k]
            if suggestions:
                for s in suggestions:
                    print(f'Você se refere a "{s}"?')
                new_name = input('Digite uma das sugestões acima ou deixe vazio para tentar encontrar um link pelo nome dado: ')
                if new_name.lower() in anime_dict:
                    name = new_name
                    continue
        else:
            data = requests.get(
                'https://drive.google.com/u/0/uc?id=1Mg8mYSwiKQJ8PGYuip9gZJG55igY6MkH&export=download',
                headers=HEADERS,
            )
            ANIME_DICT_FILE.write_bytes(data.content)
            continue

        link = f"https://animesonlinecc.to/anime/{'-'.join(name.lower().split())}/"
        r = requests.get(link, headers=HEADERS)
        if r.status_code == 200 and BeautifulSoup(r.content, "html.parser").select_one('ul.episodios'):
            answer = get_input("Quer adicionar esse anime às sugestões da busca de animes? (s/n): ", 0, 0, keys=['s', 'n'])
            if answer == 's':
                with open(ANIME_DICT_FILE, 'r') as f:
                    anime_dict = json.load(f)
                anime_dict[name.lower()] = link
                with open(ANIME_DICT_FILE, 'w') as f:
                    json.dump(anime_dict, f, indent=4)
            return link
        return False


def load_anime_list(check_new: bool = False) -> list:
    animes = []
    for file in ANIMES_DIR.iterdir():
        if file.is_file() and file.name != "anime_dict.json":
            try:
                animes.append(Anime(file))
            except json.decoder.JSONDecodeError:
                print(f"Erro: O arquivo {file} foi corrompido, por favor adicione o anime novamente.")
                file.unlink(missing_ok=True)
    if check_new:
        for anime in animes:
            if anime.needs_check():
                anime.check_episodes()
    return animes


def prompt_add_anime() -> bool:
    name = input("Digite o nome do anime a ser incluído: ")
    link = get_link_by_name(name)
    if not link:
        print("Desculpe, não foi possível obter o link pelo nome dado...")
        choice = get_input("Gostaria de digitar o link manualmente? (s/n): ", 0, 0, ['s', 'n'])
        if choice != 's':
            return False
        link = test_link("Digite o link do anime: ")
    add_anime(name, link)
    print(f'Anime "{name}" adicionado com sucesso!\n')
    return True


def show_episode_menu(anime: Anime):
    ep_keys = list(anime.episodes.keys())
    for i, episode in enumerate(ep_keys):
        marker = " *" if anime.last_episode != '' and i == anime.last_episode else ""
        print(episode + marker)
    print('Digite "*" para ir direto para o próximo episódio ou "s" para voltar ao menu principal.')
    action = get_input("\nSelecione um episódio da lista acima: ", len(anime.episodes), keys=['*', 's'])
    if action == 's':
        return
    if action == '*':
        action = 0 if anime.last_episode in ('', len(anime.episodes) - 1) else anime.last_episode + 1
    anime.call(action)


def handle_cli(anime_list: list) -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", type=int, nargs='+', dest="anime")
    args = parser.parse_args()
    if not args.anime:
        return False
    idx = args.anime[0] - 3
    if len(args.anime) == 1:
        try:
            anime_list[idx].call()
        except IndexError:
            print("Erro: Nenhum anime registrado no número dado.")
    elif len(args.anime) == 2:
        try:
            anime = anime_list[idx]
            anime.get_episodes()
            anime.call(args.anime[1] - 1)
        except IndexError:
            print("Erro: Nenhum anime registrado no número dado ou número de episódio inválido!")
    else:
        print(f"Erro: Esperado no máximo 2 argumentos mas {len(args.anime)} foram passados")
    return True


def main():
    if not ANIMES_DIR.is_dir():
        print("Bem-Vindo ao Animan!")
        name = input("Por favor, digite o nome do primeiro anime a ser incluído: ")
        ANIMES_DIR.mkdir()
        link = get_link_by_name(name)
        if not link:
            print("Desculpe, não foi possível obter o link pelo nome dado...")
            choice = get_input("Gostaria de digitar o link manualmente? (s/n): ", 0, 0, ['s', 'n'])
            if choice == 's':
                link = test_link("Digite o link do anime: ")
            else:
                sys.exit()
        add_anime(name, link)
        print(f'Anime "{name}" adicionado com sucesso!\n')

    anime_list = load_anime_list(check_new=True)

    if handle_cli(anime_list):
        return

    while True:
        print()
        print('Escolha um anime:')
        anime_list.sort(key=lambda x: x.name)
        for n, anime in enumerate(anime_list):
            suffix = "\t(Novo Episódio!)" if anime.new_episode else ""
            print(f"{n + 1}. {anime.name}{suffix}")
        print('Digite "a" para adicionar um anime, "r" para remover ou "s" para sair do programa.')

        action = get_input("> ", len(anime_list), keys=["a", "r", "s"])
        print()

        if action == "a":
            prompt_add_anime()
            anime_list = load_anime_list()
        elif action == "r":
            anime_num = get_input("Qual anime você quer remover?\n> ", len(anime_list), 1)
            anime = anime_list[anime_num]
            if remove_anime(anime):
                print(f'Anime "{anime.name}" removido com sucesso!\n')
                anime_list = load_anime_list()
        elif action == "s":
            sys.exit()
        else:
            anime = anime_list[action]
            print(f'Episódios disponíveis para "{anime.name}":')
            anime.get_episodes()
            show_episode_menu(anime)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo usuário.")
    except requests.exceptions.ConnectionError:
        print("Erro: Verifique sua conexão com a internet!")
    except json.decoder.JSONDecodeError:
        print(f"Erro: Os arquivos do programa foram corrompidos, por favor delete o arquivo "
              f"{ANIME_DICT_FILE} e tente novamente.")
