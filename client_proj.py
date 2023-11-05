import random
import threading
import pickle
import socket
import os
import io
import tkinter

try:
    from PIL import Image, ImageTk
except ImportError:
    os.system('python -m pip install Pillow')
    from PIL import Image, ImageTk
try:
    import pygame
except ImportError:
    os.system('python -m pip install pygame')
    import pygame

try:
    from mutagen.mp3 import MP3
except ImportError:
    os.system('python -m pip install mutagen')
    from mutagen.mp3 import MP3

try:
    import customtkinter as ctk
except ImportError:
    os.system('python -m pip install customtkinter')
    import customtkinter as ctk
try:
    import pytube
except ImportError or ModuleNotFoundError:
    os.system("pip install pytube")
    import pytube

try:
    from moviepy.editor import *
except ImportError or ModuleNotFoundError:
    os.system("pip install moviepy")
    from moviepy.editor import *

try:
    import cryptography
except ModuleNotFoundError:
    os.system("pip install cryptography")
    import cryptography
from cryptography.fernet import Fernet

try:
    import rsa
except ModuleNotFoundError:
    os.system("pip install rsa")
    import rsa
import pickle

try:
    import pyaes
except ModuleNotFoundError:
    os.system("pip install pyaes")
    import pyaes

import time
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

event_thread = threading.Event()
NUM_PLAYLIST = 0
SERVER_IP = "127.0.0.1"
QA_IMG_LOC = r"enter-screen.png"
MAIN_FIRST_TIME_FLAG = True
PAUSED = True
STOPPED = True
CURRENT_SONG = ''
"""add current playing song name for queue"""
"""4000 packets works"""


class Event(object):

    def __init__(self):
        self.handlers = []

    def add(self, handler):
        self.handlers.append(handler)
        return self

    def remove(self, handler):
        self.handlers.remove(handler)
        return self

    def fire(self, sender, earg=None):
        for handler in self.handlers:
            handler(sender, earg)

    __iadd__ = add
    __isub__ = remove
    __call__ = fire


class Publisher(object):

    def __init__(self):
        # Set event object
        self.evt_foo = Event()

    def foo(self):
        # Call event object with self as a sender
        self.evt_foo(self)


class ResetMain(threading.Thread):
    def __init__(self, scroll_playlist, scroll_user, ser_sk, playlist_page_function, create_active_user_page):
        threading.Thread.__init__(self)
        self.scroll_playlist = scroll_playlist
        self.scroll_user = scroll_user
        self.server_socket = ser_sk
        self.create_playlist_page = playlist_page_function
        self.create_active_user_page = create_active_user_page

    def run(self):

        """Reset the main screen by using threads"""
        global NUM_PLAYLIST
        self.server_socket.send("MaximumPlaylist".encode())
        max_playlist = self.server_socket.recv(1024).decode()
        scroll_playlist_list_len = len(self.scroll_playlist.winfo_children())
        NUM_PLAYLIST = int(max_playlist)
        for i in range(NUM_PLAYLIST - scroll_playlist_list_len):
            num_playlist = str(i + 1 + scroll_playlist_list_len)
            button = ctk.CTkButton(self.scroll_playlist,
                                   command=lambda x=num_playlist: self.create_playlist_page(x, " "),
                                   text=f"Playlist #{num_playlist}", fg_color="#1b1b1c",
                                   font=ctk.CTkFont(family="Cooper BLack"))
            button.pack()

        self.server_socket.send("Get-Active".encode())
        active_users = self.server_socket.recv(1024)
        active_users = pickle.loads(active_users)
        scroll_user_list_active = []
        for butt in self.scroll_user.winfo_children():
            if not butt.cget("text") in active_users:
                butt.configure(state="disabled")
            if butt.cget("text") in active_users and butt.cget("state") == "disabled":
                butt.configure(state="normal")
            scroll_user_list_active.append(butt.cget("text"))
        for i in range(len(active_users)):
            if active_users[i] not in scroll_user_list_active:
                button = ctk.CTkButton(self.scroll_user,
                                       command=lambda x=active_users[i]: self.create_active_user_page(x),
                                       text=f"{active_users[i]}"
                                       , fg_color="#1b1b1c", font=ctk.CTkFont(family="Cooper BLack"))
                button.pack()


class MusicThread(threading.Thread):
    def __init__(self, ser_socket, song_length, p_p_button, slider, bar, stop_func):
        threading.Thread.__init__(self)
        self.song_length_byte = song_length
        self.server_socket = ser_socket
        self.play_pause_button = p_p_button
        self.my_slider = slider
        self.status_bar = bar
        self.stop = stop_func

    def run(self):
        global STOPPED
        global PAUSED
        """recvives messagaes from clients to check whether some one found the number
        data = b""
        count = 1
        len_song_from_data = 0
        while self.song_length != len_song_from_data:
            packet = self.server_socket.recv(1024)
            if count % 2000 == 0:
                queue.append(data)
                data = b""
            if count == 4000:
                thread_play = PlayThread()
                thread_play.start()
                print("started")
            count += 1
            data += packet
            len_song_from_data += len(packet)
            print(self.song_length, len_song_from_data)
        print("made")"""
        try:
            pygame.mixer.music.stop()
            STOPPED = False
            button_picture = tk.PhotoImage(file=r"pause.png")
            self.play_pause_button.configure(image=button_picture)
            self.play_pause_button.image = button_picture
            PAUSED = False
            start_time = time.time()
            received_payload = b""
            reamining_payload_size = self.song_length_byte
            while reamining_payload_size != 0:
                print(type(received_payload))
                print(type(reamining_payload_size))
                received_payload += self.server_socket.recv(int(reamining_payload_size))
                reamining_payload_size = int(self.song_length_byte) - len(received_payload)
            packet = received_payload
            end_time = time.time()
            print(end_time - start_time)
            start_time = time.time()

            with open('music.mp3', 'wb') as f:
                f.write(packet)
            f.close()
            end_time = time.time()
            print(end_time - start_time)
            pygame.mixer.music.load('music.mp3')
            pygame.mixer.music.play(loops=0)
            song_mut = MP3('music.mp3')
            song_len = song_mut.info.length

            while (pygame.mixer.music.get_busy() or PAUSED) and not STOPPED:
                current_time = pygame.mixer.music.get_pos() / 1000
                converted_current_time = time.strftime('%M:%S', time.gmtime(current_time))
                # Get song Length
                # Convert to Time Format
                converted_song_length = time.strftime('%M:%S', time.gmtime(song_len))
                current_time += 1

                if int(self.my_slider.get()) == int(song_len):
                    self.status_bar.configure(
                        text=f'Time Elapsed: {converted_current_time}  of  {converted_song_length}  ')
                elif PAUSED:
                    pass
                elif int(self.my_slider.get()) == int(current_time):
                    # Update Slider To position
                    slider_position = int(song_len)
                    self.my_slider.configure(to=slider_position)
                    self.my_slider.set(int(current_time))

                else:
                    # Update Slider To position
                    slider_position = int(song_len)
                    self.my_slider.configure(to=slider_position)
                    self.my_slider.set(int(self.my_slider.get()))
                    # convert to time format
                    converted_current_time = time.strftime('%M:%S', time.gmtime(int(self.my_slider.get())))

                    # Output time to status bar
                    self.status_bar.configure(
                        text=f'Time Elapsed: {converted_current_time}  of  {converted_song_length}  ')

                    # Move this thing along by one second
                    next_time = int(self.my_slider.get()) + 1
                    self.my_slider.set(next_time)
                time.sleep(1)
            pygame.mixer.music.unload()
            try:
                os.remove("music.mp3")
            except PermissionError:
                pass
            print(int(self.my_slider.get()))
            print(int(song_len) // 1)
            if not pygame.mixer.music.get_busy() and (int(self.my_slider.get()) == int(song_len) // 1 - 1 or
                                                      int(self.my_slider.get()) == int(song_len)) // 1:
                self.stop()
            self.status_bar.configure(text='Time Elapsed: 00:00 of 00:00')
            self.my_slider.set(0)
            print("removed")
        except Exception as e:
            print(e)


class SearchBarThread(threading.Thread):
    def __init__(self, search_bar, listbox, ser_sk):
        threading.Thread.__init__(self)
        self.search_bar = search_bar
        self.listbox = listbox
        self.server_socket = ser_sk

    def run(self):
        """uses search bar to search a song from the server database"""
        search_song = self.search_bar.get()
        self.server_socket.send("Search-Song".encode())
        data = self.server_socket.recv(1024).decode()
        while data != 'OK':
            self.server_socket.send("Search-Song".encode())
            data = server_socket.recv(1024)
        self.listbox.delete(0, tk.END)
        self.server_socket.send(search_song.encode())
        data = self.server_socket.recv(1024)
        if data == b'':
            self.listbox.insert(ctk.END, "No Song Found")
        else:
            list_song = pickle.loads(data)
            for item in list_song:
                self.listbox.insert(ctk.END, item)


class GetSongsThread(threading.Thread):
    def __init__(self, scroll, button, num_playlist, ser_sk, listening_process, show_menu, user):
        threading.Thread.__init__(self)
        self.scroll = scroll
        self.search_button = button
        self.num_playlist = num_playlist
        self.server_socket = ser_sk
        self.listening_process = listening_process
        self.show_menu = show_menu
        self.user = user

    def run(self):
        """gets a list of songs and creates play buttons"""
        print("GetThread")
        if self.user == " ":
            self.server_socket.send("Get-Songs-Self".encode())
        else:
            self.server_socket.send("Get-Songs-Other".encode())
            self.server_socket.recv(1024)
            self.server_socket.send(self.user.encode())
        self.server_socket.recv(1024).decode()
        self.server_socket.send(str(self.num_playlist).encode())
        data_len = self.server_socket.recv(1024).decode()
        print(data_len)
        self.server_socket.send("OK".encode())
        received_payload = b""
        reamining_payload_size = data_len
        while reamining_payload_size != 0:
            print(type(received_payload))
            print(type(reamining_payload_size))
            received_payload += self.server_socket.recv(int(reamining_payload_size))
            reamining_payload_size = int(data_len) - len(received_payload)
        data_arr = pickle.loads(received_payload)
        print("got to play")
        create_play_buttons(self.scroll, data_arr, self.search_button, self.listening_process, self.show_menu)


class SignUpThread(threading.Thread):
    def __init__(self, first_txt, second_txt, message_txt, ser_sk):
        threading.Thread.__init__(self)
        self.first_txt = first_txt
        self.second_txt = second_txt
        self.message_txt = message_txt
        self.server_socket = ser_sk

    def run(self):
        """send sign up protocoal to server and encrypts password"""
        self.server_socket.send("Sign-Up".encode())
        self.server_socket.recv(1024)
        user_name = self.first_txt.get()
        self.server_socket.send(user_name.encode())
        self.server_socket.recv(1024)
        aesmess = "This_key_for_demo_purposes_only!"  # מחרוזת, ממנה יווצר מפתח סימטריי
        aeskey = aesmess.encode('utf-8')
        aes = pyaes.AESModeOfOperationCTR(aeskey)
        password = self.second_txt.get()
        ciphertext = aes.encrypt(password)  # הצפנה של ההודעה ע"י המפתח הסומטרי
        self.server_socket.send(ciphertext)  # שליחתה לשרת
        mess = self.server_socket.recv(1024).decode()
        self.message_txt.configure(text=mess)
        self.first_txt.delete(0, tk.END)
        self.second_txt.delete(0, tk.END)


class LoginThread(threading.Thread):
    def __init__(self, first_txt, second_txt, message_txt, server_sk, main_wn, main_screen_function):
        threading.Thread.__init__(self)
        self.first_txt = first_txt
        self.second_txt = second_txt
        self.message_txt = message_txt
        self.server_socket = server_sk
        self.main_wind = main_wn
        self.create_main_screen = main_screen_function

    def run(self):
        """send log in protocol to server and logs in"""
        self.server_socket.send("login".encode())
        self.server_socket.recv(1024)
        user_name = self.first_txt.get()
        password = self.second_txt.get()
        while len(user_name) == 0 or len(password) == 0:
            user_name = first_txt.get()
            print(user_name)
            password = second_txt.get()
            print(password)
        self.server_socket.send(user_name.encode())
        self.server_socket.recv(1024)
        aesmess = "This_key_for_demo_purposes_only!"  # מחרוזת, ממנה יווצר מפתח סימטריי
        aeskey = aesmess.encode('utf-8')
        aes = pyaes.AESModeOfOperationCTR(aeskey)
        plaintext = password
        ciphertext = aes.encrypt(plaintext)  # הצפנה של ההודעה ע"י המפתח הסומטרי
        self.server_socket.send(ciphertext)  # שליחתה לשרת
        mess = self.server_socket.recv(1024).decode()
        self.message_txt.configure(text=mess)
        if mess == "Success!":
            self.main_wind.clear_screen(False, "", "", "", "", "")
            pub = Publisher()
            pub.evt_foo += self.create_main_screen
            pub.foo()


class InsertToPlaylist(threading.Thread):
    def __init__(self, num_playlist, song_title, ser_sk):
        threading.Thread.__init__(self)
        self.num_playlist = num_playlist
        self.song_title = song_title
        self.server_socket = ser_sk

    def run(self):
        """Insert given song to playlist"""
        self.server_socket.send("Insert-Playlist".encode())
        data = self.server_socket.recv(1024).decode()
        while data != 'OK':
            self.server_socket.send("Insert-Playlist".encode())
            data = self.server_socket.recv(1024).decode()
        playlist_list = [self.song_title, self.num_playlist]
        p_list = pickle.dumps(playlist_list)
        self.server_socket.send(p_list)


class Window:
    def __init__(self, win_name, width, height):
        self.win = ctk.CTk()
        self.win.geometry("%dx%d" % (width, height))
        self.win.title(win_name)
        self.win.resizable(width=ctk.FALSE, height=ctk.FALSE)
        self.photo = None
        self.win_width = width
        self.win_height = height

    def change_exit_protocol(self, exit_func, ser_sock):
        self.win.protocol("WM_DELETE_WINDOW", lambda: exit_func(ser_sock))

    def get_win(self):
        """gets the window"""
        return self.win

    def create_canvas(self):
        """creates canvas"""
        cnvs = tk.Canvas(self.win, width=400, height=400)
        return cnvs

    @staticmethod
    def create_label(frame, text):
        lbl = ctk.CTkLabel(frame, text=text, fg_color="transparent", anchor=tk.W)
        return lbl

    @staticmethod
    def create_button(master, command, img, bg_color):
        """
        button_picture = ctk.CTkImage(Image.open(img), None, (width, height))
        button = ctk.CTkButton(master=self.win, command=command, image=button_picture,
                               compound="left", bg_color=bg_color, fg_color=fg_color, hover_color=bg_color, text=text,
                               corner_radius=corner_radius, border_width=border_width)
        """

        button_picture = tk.PhotoImage(file=img)
        button = tk.Button(master, command=command, image=button_picture, borderwidth=0, bg=bg_color)
        button.image = button_picture
        return button

    def create_entry_label(self, x, y, shows, fg_color, bg_color, place_text, width, height):
        """creates entry"""
        ent = ctk.CTkEntry(master=self.win, show=shows, fg_color=fg_color, bg_color=bg_color,
                           placeholder_text=place_text, width=width, height=height)
        ent.place(x=x, y=y, anchor="center")
        ent.focus_set()
        return ent

    def create_picture(self, pic, width, height, x, y):
        """creates pictures"""
        self.photo = ctk.CTkImage(Image.open(pic), None, (width, height))
        lbl = ctk.CTkLabel(self.win, image=self.photo, text="", anchor=tk.NW)
        lbl.image = self.photo
        lbl.place(x=x, y=y)
        return lbl

    def clear_screen(self, flag, side_frame, music_frame, main_background, play_button_menu, play_button_menu_label):
        """cleares the screen except certain elemants if flag is raised"""
        for widget in self.win.winfo_children():
            if flag is True and widget in [side_frame, music_frame, main_background,
                                           play_button_menu, play_button_menu_label]:
                print(widget)
            else:
                widget.destroy()

    def loop(self):
        """loops the app"""
        self.win.mainloop()

    @staticmethod
    def create_time_bar(frame):
        """creates timebar"""
        time_bar = ctk.CTkLabel(frame, text='Time Elasped: 00:00 of 00:00', anchor=ctk.CENTER, width=800)
        return time_bar

    @staticmethod
    def create_scale(frame, command, width):
        """creates scale"""
        # Create Music Position Slider
        slider = ctk.CTkSlider(frame, from_=0, to=100, orientation=ctk.HORIZONTAL, command=command, width=width)
        slider.set(0)
        return slider

    @staticmethod
    def create_scroll(fr, width, height):
        """creates container"""
        container = ctk.CTkScrollableFrame(fr, width=width, height=height)
        return container

    def create_listbox(self, x, y):
        """creates listbox"""
        my_list = tk.Listbox(self.win, width=50, height=5)
        my_list.place(x=x, y=y)
        return my_list

    def create_frame(self, fg, bc, x, y):
        """creates frame"""
        cf = ctk.CTkFrame(master=self.win, fg_color=fg, border_color=bc)
        cf.place(x=x, y=y)
        return cf

    def create_dropmenu(self):
        """createsmenu"""
        menu = tk.Menu(self.win, tearoff=0)
        return menu


def create_play_buttons(scroll, list_songs, search_button, listening_process, show_menu):
    """create play button used to play songs"""
    j = 0
    for i in list_songs:
        print()
        artist_and_song = i[3]
        print(artist_and_song)
        button_picture = ImageTk.PhotoImage(Image.open("playsong.png"))

        button = ctk.CTkButton(scroll, command=lambda param=artist_and_song: listening_process(param),
                               image=button_picture, text="", fg_color="#1b1b1c")
        e = tk.Event()
        button.bind("<Button-3>", lambda e, x=artist_and_song: show_menu(e, x))
        button.image = button_picture
        button.grid(row=j, column=0)
        lbl = ctk.CTkLabel(scroll, text=artist_and_song, width=300)
        lbl.grid(row=j, column=1)
        j += 1
    search_button['state'] = ctk.NORMAL


def add_to_playlist(event, num_playlist, song_title, ser_sk):
    """adds song to a playlist"""
    insert_thread = InsertToPlaylist(num_playlist, song_title, ser_sk)
    insert_thread.setDaemon(True)
    insert_thread.start()


def search_songs_button(search_bar, listbox, ser_sk):
    """search a song in server's database"""
    search_t = SearchBarThread(search_bar, listbox, ser_sk)
    search_t.setDaemon(True)
    search_t.start()


def exit_function(ser_sock):
    """exit the app"""
    ser_sock.send("Disconnect".encode())
    ser_sock.close()
    sys.exit()


def sign_up(first_txt, second_txt, message_txt, ser_sk):
    """creates sign up thread """
    if len(first_txt.get()) > 0 and len(second_txt.get()) > 0:
        sign_thread = SignUpThread(first_txt, second_txt, message_txt, ser_sk)
        sign_thread.start()
    else:
        print("One of the Entrys are Empty")


def login(first_txt, second_txt, message_txt, server_sk, main_wn, main_screen):
    """creates login thread"""
    if len(first_txt.get()) > 0 and len(second_txt.get()) > 0:
        login_thread = LoginThread(first_txt, second_txt, message_txt, server_sk, main_wn, main_screen)
        login_thread.start()
    else:
        print("One of the Entrys are Empty")


class Client:
    def __init__(self):
        self.server_socket = socket.socket()
        self.server_socket.connect((SERVER_IP, 6969))
        self.QUEUE = []
        pygame.mixer.init()
        self.main_wind = Window("Login", 800, 600)

        self.main_background = None
        self.volume_meter = None
        self.music_frame = None
        self.my_slider = None
        self.status_bar = None
        self.playlist_scroll = None
        self.play_pause_button = None
        self.side_frame = None
        self.current_song_label = None
        self.play_button_menu_label = None
        self.play_button_menu = None
        self.active_user_scroll = None
        self.CURRENT_SONG = ""

    def reset_main(self):
        """updates main screen by thread"""
        self.main_wind.get_win().title("Main Screen")
        p_thread = ResetMain(self.playlist_scroll, self.active_user_scroll, self.server_socket,
                             self.create_playlist_page, self.create_random_active_user_page)
        p_thread.setDaemon(True)
        p_thread.start()

    def create_entrance_screen(self):
        """creates the opening screen"""
        self.main_wind.change_exit_protocol(exit_function, self.server_socket)
        self.main_wind.create_picture(QA_IMG_LOC, 800, 600, 0, 0)
        first_txt = self.main_wind.create_entry_label(385, 133, "", "#7b6d60", "#7b6d60", "Enter Your Username", 250,
                                                      20)
        second_txt = self.main_wind.create_entry_label(385, 190, "*", "#7b6d60", "#7b6d60", "Enter Your Password", 250,
                                                       20)
        message_text = self.main_wind.create_label(self.main_wind.get_win(), "")
        message_text.configure(font=("lucida", 12), fg_color="#988b7b", bg_color="#988b7b", anchor=tk.CENTER)
        message_text.place(x=355, y=210)
        sign_pht = r"signbutton.png"
        login_pht = r"key1.png"
        sign_button = self.main_wind.create_button(self.main_wind.get_win(),
                                                   lambda: sign_up(first_txt, second_txt, message_text,
                                                                   self.server_socket),
                                                   sign_pht,
                                                   "#988b7b")
        sign_button.place(x=430, y=210)
        login_button = self.main_wind.create_button(self.main_wind.get_win(), lambda: login(first_txt, second_txt
                                                                                            , message_text
                                                                                            , self.server_socket
                                                                                            , self.main_wind,
                                                                                            self.create_main_screen)
                                                    , login_pht, "#988b7b")
        login_button.place(x=260, y=210)

    def add_to_queue(self, place):
        """adds to queue"""
        label_text = self.play_button_menu_label.cget('text')
        print(label_text, "is label text")
        if place == "Next":
            print(self.CURRENT_SONG)
            if self.CURRENT_SONG == '':
                self.QUEUE.insert(0, label_text)
            else:
                index_song = self.QUEUE.index(self.CURRENT_SONG)
                self.QUEUE.insert(index_song + 1, label_text)
        else:
            self.QUEUE.append(label_text)
        print(self.QUEUE)

    def create_main_screen(self, sender, earg):
        """creates all object in main screen"""
        self.main_wind.get_win().title("Main Screen")
        self.main_background = self.main_wind.create_picture("main_uncut.png", 656, 505, 144, 0)
        self.music_frame = self.main_wind.create_frame("#000000", "#000000", 0, 505)
        skip_left_button = self.main_wind.create_button(self.music_frame, lambda: self.skip("left"), r"skipleft.png",
                                                        "#000000")
        skip_left_button.grid(row=0, column=16)
        self.play_pause_button = self.main_wind.create_button(self.music_frame, self.pause, r"play.png", "#000000")
        self.play_pause_button.grid(row=0, column=17)
        stop_button = self.main_wind.create_button(self.music_frame, self.stop, "stop.png", "#000000")
        stop_button.grid(row=0, column=18)
        skip_right_button = self.main_wind.create_button(self.music_frame, lambda: self.skip("right"), r"skipright.png",
                                                         "#000000")
        skip_right_button.grid(row=0, column=19)
        mute_button = self.main_wind.create_button(self.music_frame, self.mute, r"volume.png", "#000000")
        mute_button.grid(row=1, column=1)
        queue_button = self.main_wind.create_button(self.music_frame, self.open_queue, r"queue.png", "#000000")
        queue_button.grid(row=1, column=0)
        self.status_bar = self.main_wind.create_time_bar(self.music_frame)
        self.my_slider = self.main_wind.create_scale(self.music_frame, self.slide, 250)
        self.my_slider.grid(row=1, column=8, rowspan=1, columnspan=20)
        self.status_bar.grid(row=2, column=0, rowspan=1, columnspan=51)
        self.volume_meter = self.main_wind.create_scale(self.music_frame, self.change_volume, 150)
        self.volume_meter.grid(row=1, column=2, rowspan=1, columnspan=4)
        self.current_song_label = self.main_wind.create_label(self.music_frame, f"Now Playing : {self.CURRENT_SONG}")
        self.current_song_label.grid(row=0, column=25, rowspan=3, columnspan=20)
        self.side_frame = self.main_wind.create_frame("#1b1b1c", "#1b1b1c", 0, 0)
        back_menu_button = self.main_wind.create_button(self.side_frame, self.go_to_main, r"back.png", "#1b1b1c")
        back_menu_button.grid(row=0, column=0)
        add_song_button = self.main_wind.create_button(self.side_frame, self.send_song_url, r"addsong.png", "#1b1b1c")
        add_song_button.grid(row=1, column=0)
        add_playlist_button = self.main_wind.create_button(self.side_frame, self.create_playlist, r"addplaylist1.png",
                                                           "#1b1b1c")
        add_playlist_button.grid(row=1, column=1)
        mp3_button = self.main_wind.create_button(self.side_frame, self.upload_song, r"mp3.png", "#1b1b1c")
        mp3_button.grid(row=1, column=2)
        self.playlist_scroll = self.main_wind.create_scroll(self.side_frame, 144, 362)
        self.playlist_scroll.grid(row=2, column=0, columnspan=3)
        self.playlist_scroll.configure(fg_color="#1b1b1c")
        self.active_user_scroll = self.main_wind.create_scroll(self.side_frame, 96, 48)
        self.active_user_scroll._scrollbar.configure(height=48)
        self.active_user_scroll.grid(row=0, column=1, columnspan=2)
        self.active_user_scroll.configure(fg_color="#1b1b1c")
        self.play_button_menu = self.main_wind.create_dropmenu()
        self.play_button_menu_label = ctk.CTkLabel(self.main_wind.get_win(), text="")
        self.play_button_menu.add_command(label="Play Next", command=lambda: self.add_to_queue("Next"))
        self.play_button_menu.add_command(label="Play Last", command=lambda: self.add_to_queue("Last"))

        self.reset_main()

    def go_to_main(self):
        """reset the main screen"""
        self.main_wind.clear_screen(True, self.side_frame, self.music_frame,
                                    self.main_background, self.play_button_menu, self.play_button_menu_label)
        self.reset_main()

    def create_playlist_page(self, num_of_playlist, user):
        """creates a playlist page for a given user and playlist"""
        self.main_wind.clear_screen(True, self.side_frame, self.music_frame,
                                    self.main_background, self.play_button_menu, self.play_button_menu_label)
        self.main_wind.get_win().title("Playlist Page")
        # main_wind.create_picture("main_uncut.png", 800, 505, 0, 0)
        search_bar_playlist = self.main_wind.create_entry_label(400, 50, "", "#7b6d60", "#7b6d60", "Search A Song", 250,
                                                                20)
        listbox = self.main_wind.create_listbox(250, 100)

        song_scroll = self.main_wind.create_scroll(self.main_wind.get_win(), 580, 150)
        song_scroll.place(x=198, y=293)
        song_scroll.configure(fg_color="#1b1b1c")

        search_button_pic = r"maglass.png"
        search_button = self.main_wind.create_button(self.main_wind.get_win(),
                                                     lambda: search_songs_button(search_bar_playlist,
                                                                                 listbox, self.server_socket)
                                                     , search_button_pic, "#000000")
        search_button.place(x=505, y=39)
        # need to pass only event
        listbox.bind("<<ListboxSelect>>", lambda eff: add_to_playlist(eff, num_of_playlist, listbox.get(ctk.ACTIVE),
                                                                      self.server_socket))
        print(f"get songs thread {num_of_playlist}")
        t = GetSongsThread(song_scroll, search_button, num_of_playlist,
                           self.server_socket, self.listening_process, self.show_menu, user)
        t.setDaemon(True)
        t.start()
        search_button['state'] = ctk.DISABLED

    def create_playlist(self):
        """a middle function used to open a playtlist page"""
        # in a given frame, adds to a count of playlist, then jumps to the playlist screen to add songs
        global NUM_PLAYLIST
        self.main_wind.clear_screen(True, self.side_frame, self.music_frame,
                                    self.main_background, self.play_button_menu, self.play_button_menu_label)
        self.create_playlist_page(NUM_PLAYLIST + 1, " ")

    def skip(self, direction):
        """skips a song in queue according to given direction"""
        if self.CURRENT_SONG == '':
            pass
        else:
            index_current = self.QUEUE.index(self.CURRENT_SONG)
            print(index_current)
            if direction == "left":
                if index_current == 0:
                    self.listening_process(self.CURRENT_SONG)
                else:
                    wanted_song = self.QUEUE[index_current - 1]
                    print(wanted_song)
                    self.listening_process(wanted_song)
            else:
                if self.CURRENT_SONG == self.QUEUE[-1]:
                    self.listening_process(self.CURRENT_SONG)
                else:
                    wanted_song = self.QUEUE[index_current + 1]
                    print(wanted_song)
                    self.listening_process(wanted_song)

    def mute(self):
        """mutes a song"""
        self.volume_meter.set(0)
        pygame.mixer.music.set_volume(0)

    def open_queue(self):
        """open a menu that shows the queue"""
        self.main_wind.clear_screen(True, self.side_frame, self.music_frame,
                                    self.main_background, self.play_button_menu, self.play_button_menu_label)
        queue_scroll = self.main_wind.create_scroll(self.main_wind.get_win(), 580, 150)
        queue_scroll.place(x=198, y=293)
        queue_scroll.configure(fg_color="#1b1b1c")
        head_line = ctk.CTkLabel(queue_scroll, text="Your Queue:")
        head_line.pack()
        for i in self.QUEUE:
            lbl = ctk.CTkLabel(queue_scroll, text=i)
            lbl.pack()

    def change_volume(self, x):
        """changes the volume of a song"""
        meter_value = self.volume_meter.get() / 100
        pygame.mixer.music.set_volume(meter_value)

    def pause(self):
        """pause and unpause accordingly to a flag """
        global PAUSED
        if PAUSED:
            # Unpause
            pygame.mixer.music.unpause()
            button_picture = tk.PhotoImage(file=r"pause.png")
            self.play_pause_button.configure(image=button_picture)
            self.play_pause_button.image = button_picture
            PAUSED = False
            if not self.QUEUE:
                pass
            elif self.CURRENT_SONG == '' and self.QUEUE[0] != '':
                self.listening_process(self.QUEUE[0])
        else:
            # Pause
            pygame.mixer.music.pause()
            button_picture = tk.PhotoImage(file=r"play.png")
            self.play_pause_button.configure(image=button_picture)
            self.play_pause_button.image = button_picture
            PAUSED = True

    def stop(self):
        """stops the song from running"""
        global STOPPED
        # Stop Song From Playing
        pygame.mixer.music.stop()
        # Reset Slider and Status Bar
        self.status_bar.configure(text='Time Elapsed: 00:00 of 00:00')
        self.my_slider.set(0)
        self.current_song_label.configure(text="Now Playing : ")
        STOPPED = True
        if not PAUSED:
            self.pause()
        self.CURRENT_SONG = ''
        print(STOPPED, PAUSED)

    def slide(self, x):
        """used for skiping parts of a song by draging slider"""
        # slider_label.config(text=f'{int(my_slider.get())} of {int(song_length)}')
        # song = song_box.get(ACTIVE)
        # song = f'C:/gui/audio/{song}.mp3'
        if pygame.mixer.music.get_busy():
            # pygame.mixer.music.load("music.mp3")
            pygame.mixer.music.play(loops=0, start=int(self.my_slider.get()))
        else:
            try:
                pygame.mixer.music.play(loops=0, start=int(self.my_slider.get()))
                pygame.mixer.music.pause()
            except pygame.error:
                pass

    def send_song(self, artist_name, song_name, song):
        """send song to server with given song name and artist """
        self.server_socket.send("upload".encode())
        self.server_socket.recv(2)
        artist_and_song = artist_name + "-" + song_name
        self.server_socket.send(artist_and_song.encode())
        self.server_socket.recv(2)
        song_length = str(len(song))
        self.server_socket.send(song_length.encode())
        print(type(song_length))
        self.server_socket.recv(2)
        self.server_socket.send(song)

    def upload_song(self):
        """uploads a mp3 to server"""
        try:
            filename = filedialog.askopenfilename()
            file = open(filename, "rb")
            sound = file.read()
            artist_name_dialog = ctk.CTkInputDialog(text="Type in a Artist:", title="Artist")
            artist_name = artist_name_dialog.get_input()
            song_name_dialog = ctk.CTkInputDialog(text="Type in a Song Name:", title="Song Name")
            song__name = song_name_dialog.get_input()
            self.send_song(artist_name, song__name, sound)
        except FileNotFoundError:
            pass

    def listening_process(self, artist_and_song):
        """manages the listening part of a song with the server"""
        self.status_bar.configure(text='Time Elapsed: 00:00 of 00:00')
        self.my_slider.set(0)
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()

            print("stopped")
        self.server_socket.send("listen".encode())
        self.server_socket.recv(1024)
        self.server_socket.send(artist_and_song.encode())
        song_length = int(self.server_socket.recv(1024).decode())
        self.server_socket.send("OK".encode())
        self.CURRENT_SONG = artist_and_song
        if self.CURRENT_SONG not in self.QUEUE:
            self.QUEUE.insert(1, self.CURRENT_SONG)
        self.current_song_label.configure(text=f"Now Playing : {self.CURRENT_SONG}")
        rec_thread = MusicThread(self.server_socket, song_length,
                                 self.play_pause_button, self.my_slider, self.status_bar, self.stop)
        rec_thread.setDaemon(True)
        rec_thread.start()

        # pub = Publisher()
        # pub.evt_foo += create_main_screen
        # pub.foo()

    def show_menu(self, event, artist_song):
        """controls the menu for adding to queue"""
        print(event, artist_song)
        self.play_button_menu.post(event.x_root, event.y_root)
        self.play_button_menu_label.configure(text=artist_song)

    def send_song_url(self):
        """from a given url sends to server and uploads a song from the intenet"""
        song_url_dialog = ctk.CTkInputDialog(text="Type A Youtube URL of a Song:", title="URL Song")
        song_url = song_url_dialog.get_input()
        artist_name_dialog = ctk.CTkInputDialog(text="Type in a Artist:", title="Artist")
        artist_name = artist_name_dialog.get_input()
        song_name_dialog = ctk.CTkInputDialog(text="Type in a Song Name:", title="Song Name")
        song_name = song_name_dialog.get_input()
        self.server_socket.send("Url-Download".encode())
        self.server_socket.recv(1024)
        self.server_socket.send(song_url.encode())
        self.server_socket.recv(1024)
        self.server_socket.send(song_name.encode())
        self.server_socket.recv(1024)
        self.server_socket.send(artist_name.encode())

    def create_random_active_user_page(self, user):
        """creates playlist page for other user than OG and a random playlist"""
        self.server_socket.send("MaximumPlaylist".encode())
        max_playlist = int(self.server_socket.recv(1024).decode())
        rand_num = random.randint(1, max_playlist + 1)
        self.create_playlist_page(rand_num, user)


def main():
    my_client = Client()
    my_client.create_entrance_screen()
    my_client.main_wind.loop()
    """
    answer = ""
    while answer != "Exit":
        answer = input("Do you want to upload or listen?")
        server_socket.send(answer.encode())
        if answer == "upload":
            artist_name = input("Who is the author?")
            song_name = input("What's the name of the song?")
            artist_and_song = artist_name + "-" + song_name
            filename = filedialog.askopenfilename()
            file = open(filename, "rb")
            sound = pygame.mixer.Sound(file)
            print(len(sound.get_raw()))
            server_socket.send(artist_and_song.encode())
            song_length = str(len(sound.get_raw()))
            server_socket.send(song_length.encode())
            server_socket.send(sound.get_raw())
        elif answer == "listen":
            artist_name = input("Who is the author?")
            song_name = input("What's the name of the song?")
            artist_and_song = artist_name + "-" + song_name
            server_socket.send(artist_and_song.encode())
            song_length = int(server_socket.recv(1024).decode())
            rec_thread = RecThread(server_socket, song_length)
            rec_thread.start()
            rec_thread.join()
    """


if __name__ == '__main__':
    main()
