import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

class P2PChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Peer-to-Peer Chat")
        self.conn = None
        self.server_socket = None
        self.connected = False

        top_frame = tk.Frame(root)
        top_frame.pack(padx=10, pady=10, fill="x")

        self.mode_var = tk.StringVar(value="host")

        tk.Label(top_frame, text="Mode:").grid(row=0, column=0, sticky="w")
        tk.Radiobutton(top_frame, text="Host", variable=self.mode_var, value="host", command=self.update_mode).grid(row=0, column=1, sticky="w")
        tk.Radiobutton(top_frame, text="Join", variable=self.mode_var, value="join", command=self.update_mode).grid(row=0, column=2, sticky="w")

        tk.Label(top_frame, text="Listening Port:").grid(row=1, column=0, sticky="w")
        self.listen_port_entry = tk.Entry(top_frame)
        self.listen_port_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(top_frame, text="Peer IP:").grid(row=2, column=0, sticky="w")
        self.peer_ip_entry = tk.Entry(top_frame)
        self.peer_ip_entry.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(top_frame, text="Peer Port:").grid(row=3, column=0, sticky="w")
        self.peer_port_entry = tk.Entry(top_frame)
        self.peer_port_entry.grid(row=3, column=1, padx=5, pady=2)

        self.start_button = tk.Button(top_frame, text="Start", command=self.start_chat)
        self.start_button.grid(row=4, column=0, columnspan=3, pady=10)

        self.chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state="disabled", width=50, height=20)
        self.chat_area.pack(padx=10, pady=10, fill="both", expand=True)

        bottom_frame = tk.Frame(root)
        bottom_frame.pack(padx=10, pady=10, fill="x")

        self.message_entry = tk.Entry(bottom_frame)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(bottom_frame, text="Send", command=self.send_message)
        self.send_button.pack(side="right")

        self.update_mode()

    def update_mode(self):
        mode = self.mode_var.get()

        if mode == "host":
            self.peer_ip_entry.config(state="disabled")
            self.peer_port_entry.config(state="disabled")
        else:
            self.peer_ip_entry.config(state="normal")
            self.peer_port_entry.config(state="normal")

    def append_chat(self, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, text + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state="disabled")

    def start_server(self, listen_port):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", listen_port))
            self.server_socket.listen(1)

            self.append_chat(f"Hosting chat on port {listen_port}...")
            self.append_chat("Waiting for another peer to join...")

            conn, addr = self.server_socket.accept()

            self.conn = conn
            self.connected = True

            self.append_chat(f"Peer joined from {addr[0]}:{addr[1]}")
            self.append_chat("Chat is ready.")

            threading.Thread(target=self.receive_messages, daemon=True).start()

        except Exception as e:
            self.append_chat(f"Server error: {e}")

    def connect_to_host(self, peer_ip, peer_port):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((peer_ip, peer_port))

            self.conn = client
            self.connected = True

            self.append_chat(f"Connected to host at {peer_ip}:{peer_port}")
            self.append_chat("Chat is ready.")

            threading.Thread(target=self.receive_messages, daemon=True).start()

        except Exception as e:
            self.append_chat(f"Connect error: {e}")

    def receive_messages(self):
        while True:
            try:
                msg = self.conn.recv(1024).decode()
                if not msg:
                    self.append_chat("Peer disconnected.")
                    break
                self.append_chat(f"Peer: {msg}")
            except:
                self.append_chat("Connection closed.")
                break

        self.connected = False

        try:
            if self.conn:
                self.conn.close()
        except:
            pass
        self.conn = None

        try:
            if self.server_socket:
                self.server_socket.close()
        except:
            pass
        self.server_socket = None

    def start_chat(self):
        mode = self.mode_var.get()

        if mode == "host":
            try:
                listen_port = int(self.listen_port_entry.get())
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid listening port.")
                return

            threading.Thread(target=self.start_server, args=(listen_port,), daemon=True).start()
            self.start_button.config(state="disabled")

        else:
            try:
                peer_ip = self.peer_ip_entry.get().strip()
                peer_port = int(self.peer_port_entry.get())
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid peer port.")
                return

            if not peer_ip:
                messagebox.showerror("Input Error", "Please enter the host IP.")
                return

            threading.Thread(target=self.connect_to_host, args=(peer_ip, peer_port), daemon=True).start()
            self.start_button.config(state="disabled")

    def send_message(self, event=None):
        msg = self.message_entry.get().strip()
        if not msg:
            return

        if not self.connected or self.conn is None:
            messagebox.showwarning("Not Connected", "No connection yet.")
            return

        try:
            self.conn.sendall(msg.encode())
            self.append_chat(f"You: {msg}")
            self.message_entry.delete(0, tk.END)
        except Exception as e:
            self.append_chat(f"Send error: {e}")

root = tk.Tk()
app = P2PChatGUI(root)
root.mainloop()
