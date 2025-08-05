import tkinter as tk
from PIL import Image, ImageTk
import cairosvg
import io
import requests
import chess
import chess.pgn
import random
import tkinter.messagebox
from tkinter import colorchooser
import os
import json
from tkinter import filedialog

class ChessKnightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Knight Moves")
        self.square_size = 60
        self.board_size = 8
        self.margin = 20
        self.use_green_theme = False
        self.light_color_default = "white"
        self.dark_color_default = "gray"
        self.light_color_green = "#e9e9e9"
        self.dark_color_green = "#3D6E3D"
        self.light_color = self.light_color_default
        self.dark_color = self.dark_color_default
        self.left_frame = tk.Frame(root)
        self.left_frame.pack(side=tk.LEFT, padx=10)
       
        self.canvas = tk.Canvas(self.left_frame, width=self.square_size * self.board_size + 2 * self.margin + 100,
                                height=self.square_size * self.board_size + 2 * self.margin)
        self.canvas.pack(side=tk.TOP)
        self.nav_frame = tk.Frame(self.left_frame)
        self.nav_frame.pack(pady=5)
       
        self.to_start_btn = tk.Button(self.nav_frame, text="<<", command=self.to_start, state=tk.DISABLED)
        self.to_start_btn.pack(side=tk.LEFT, padx=5)
        self.back_btn = tk.Button(self.nav_frame, text="<", command=self.back, state=tk.DISABLED)
        self.back_btn.pack(side=tk.LEFT, padx=5)
        self.forward_btn = tk.Button(self.nav_frame, text=">", command=self.forward, state=tk.DISABLED)
        self.forward_btn.pack(side=tk.LEFT, padx=5)
        self.to_end_btn = tk.Button(self.nav_frame, text=">>", command=self.to_end, state=tk.DISABLED)
        self.to_end_btn.pack(side=tk.LEFT, padx=5)
        self.current_coord = tk.StringVar()
        self.current_coord.set("Selected: None")
        self.coord_label = tk.Label(root, textvariable=self.current_coord, font=("Arial", 14))
        self.coord_label.pack(side=tk.TOP, pady=10, anchor="w")
        self.knights = [
            {"pos": [7, 1], "color": "white", "selected": False},
            {"pos": [7, 6], "color": "white", "selected": False},
            {"pos": [0, 1], "color": "black", "selected": False},
            {"pos": [0, 6], "color": "black", "selected": False},
        ]
        self.white_king_pos = [7, 4]
        self.black_king_pos = [0, 4]
        self.white_king_selected = False
        self.black_king_selected = False
        self.legal_moves = []
        self.second_moves_groups = []
        self.right_click_pos = None
        self.right_click_second_pos = None
        self.right_click_third_pos = None
        self.right_click_fourth_pos = None
        self.right_click_second_moves = []
        self.right_click_third_moves = []
        self.right_click_fourth_moves = []
        self.show_move_numbers = False
        self.history = []
        self.redo_stack = []
        self.board = chess.Board()
        self.other_pieces = []
        self.add_piece_mode = False
        self.add_piece_selected = None
        self.add_piece_square = None
        self.last_random_game_state = None
        self.last_random_game_set = False
        self.game = None
        self.move_list = []
        self.current_move = 0
        self.game_name_var = tk.StringVar()
        self.game_name_var.set("")
        self.game_name_label = tk.Label(root, textvariable=self.game_name_var, font=("Arial", 10))
        self.game_name_label.pack(side=tk.TOP, pady=2, anchor="w")
        self.to_move_var = tk.StringVar()
        self.to_move_var.set("")
        self.to_move_label = tk.Label(root, textvariable=self.to_move_var, font=("Arial", 10))
        self.to_move_label.pack(side=tk.TOP, pady=2, anchor="w")
        # --- Drag and drop state ---
        self.drag_data = {
            "piece_type": None, # Type or dict for knights/kings, or string for other pieces
            "piece_ref": None, # Reference to the moved piece
            "start_pos": None, # [row, col]
            "drag_image": None, # Canvas image used for dragging
            "offset_x": 0, # Mouse offset in px
            "offset_y": 0,
        }
        def exit_app():
            root.destroy()
       
        self.second_move_colors = ["green", "red", "purple", "orange", "cyan", "magenta", "blue", "lime"]
        self.right_click_color = "#C496B0"
        self.third_move_color = "#CDF8F8"
        self.fourth_move_color = "#F3FCFC"
        self.first_move_color = "#FFD700"

        # Load colors from config
        try:
            with open('colors.cfg', 'r') as f:
                data = json.load(f)
                self.first_move_color = data.get('first_move_color', self.first_move_color)
                self.second_move_colors = data.get('second_move_colors', self.second_move_colors)
                self.right_click_color = data.get('right_click_color', self.right_click_color)
                self.third_move_color = data.get('third_move_color', self.third_move_color)
                self.fourth_move_color = data.get('fourth_move_color', self.fourth_move_color)
                self.use_green_theme = data.get('use_green_theme', self.use_green_theme)
        except:
            pass

        if self.use_green_theme:
            self.light_color = self.light_color_green
            self.dark_color = self.dark_color_green
        else:
            self.light_color = self.light_color_default
            self.dark_color = self.dark_color_default

        button_frame = tk.Frame(root)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=15)
        def load_svg(file_path, scale_factor=1.0):
            try:
                base_size = 40
                output_size = int(base_size * scale_factor)
                png_data = io.BytesIO()
                cairosvg.svg2png(url=file_path, write_to=png_data, output_width=output_size, output_height=output_size)
                png_data.seek(0)
                image = Image.open(png_data)
                return ImageTk.PhotoImage(image)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                return None
        self.white_knight_image = load_svg("knight.svg", scale_factor=1.0)
        self.black_knight_image = load_svg("black_knight.svg", scale_factor=1.0)
        self.white_king_image = load_svg("white_king.svg", scale_factor=1.5)
        self.black_king_image = load_svg("black_king.svg", scale_factor=1.5)
        self.piece_images = {
            'P': load_svg("white_pawn.svg", scale_factor=1.0),
            'p': load_svg("black_pawn.svg", scale_factor=1.0),
            'R': load_svg("white_rook.svg", scale_factor=1.0),
            'r': load_svg("black_rook.svg", scale_factor=1.0),
            'B': load_svg("white_bishop.svg", scale_factor=1.0),
            'b': load_svg("black_bishop.svg", scale_factor=1.0),
            'Q': load_svg("white_queen.svg", scale_factor=1.0),
            'q': load_svg("black_queen.svg", scale_factor=1.0),
            'N': self.white_knight_image,
            'n': self.black_knight_image,
        }
        self.draw_board()
        self.draw_coordinates()
        self.draw_pieces()
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        # --- Bindings for drag and drop ---
        self.canvas.bind("<ButtonPress-1>", self.on_piece_press, add="+")
        self.canvas.bind("<B1-Motion>", self.on_piece_motion, add="+")
        self.canvas.bind("<ButtonRelease-1>", self.on_piece_release, add="+")
        # The other UI setup as before ...
        self.show_moves_btn = tk.Button(button_frame, text="Show 1st & 2nd Moves", command=self.show_first_and_second_moves)
        self.show_moves_btn.pack(pady=5)
        self.reset_btn = tk.Button(button_frame, text="Reset", command=self.reset)
        self.reset_btn.pack(pady=5)
        undo_redo_frame = tk.Frame(button_frame)
        undo_redo_frame.pack(pady=5)
        self.undo_btn = tk.Button(undo_redo_frame, text="Undo", command=self.undo)
        self.undo_btn.pack(side=tk.LEFT, padx=(0,2))
        self.redo_btn = tk.Button(undo_redo_frame, text="Redo", command=self.redo)
        self.redo_btn.pack(side=tk.LEFT)
        # --- Side-by-side game buttons ---
        game_btn_frame = tk.Frame(button_frame)
        game_btn_frame.pack(pady=5)
        self.random_game_btn = tk.Button(game_btn_frame, text="Add Random Game", command=self.add_random_game)
        self.random_game_btn.pack(side=tk.LEFT, padx=2)
        self.standard_game_btn = tk.Button(game_btn_frame, text="New Standard Game", command=self.new_standard_game)
        self.standard_game_btn.pack(side=tk.LEFT, padx=2)
        row_frame = tk.Frame(button_frame)
        row_frame.pack(pady=5)
        swap_colors_btn = tk.Button(row_frame, text="Swap Board Colors", command=self.swap_board_colors)
        swap_colors_btn.pack(side=tk.LEFT, padx=2)
        self.color_settings_btn = tk.Button(row_frame, text="Customize Colors", command=self.open_color_settings_window)
        self.color_settings_btn.pack(side=tk.LEFT, padx=2)
        self.add_piece_frame = tk.Frame(button_frame, relief=tk.RAISED, bd=2)
        self.add_piece_btn = tk.Button(self.add_piece_frame, text="Add Piece", command=self.toggle_add_piece_mode)
        self.add_piece_btn.grid(row=0, column=0, columnspan=5, sticky="ew")
        self.piece_grid = []
        self.piece_grid_labels = [
            ['P', 'B', 'N', 'R', 'Q'],
            ['p', 'b', 'n', 'r', 'q'],
        ]
        for r in range(2):
            row = []
            for c in range(5):
                ptype = self.piece_grid_labels[r][c]
                piece_btn = tk.Button(self.add_piece_frame, image=self.piece_images[ptype] if self.piece_images[ptype] else None,
                                    text=ptype if not self.piece_images[ptype] else "",
                                    width=50, height=50, command=lambda t=ptype: self.select_add_piece(t))
                piece_btn.grid(row=r+1, column=c, padx=2, pady=2)
                row.append(piece_btn)
            self.piece_grid.append(row)
        self.add_piece_frame.pack(pady=10, fill="x")
        pgn_btn_frame = tk.Frame(button_frame)
        pgn_btn_frame.pack(pady=5)
        self.import_pgn_btn = tk.Button(pgn_btn_frame, text="Import PGN", command=self.import_pgn)
        self.import_pgn_btn.pack(side=tk.LEFT)
        self.load_pgn_btn = tk.Button(pgn_btn_frame, text="Load PGN", command=self.load_pgn)
        self.load_pgn_btn.pack(side=tk.LEFT, padx=2)
        self.export_pgn_btn = tk.Button(pgn_btn_frame, text="Export PGN", command=self.export_pgn)
        self.export_pgn_btn.pack(side=tk.LEFT, padx=2)
       
        exit_button = tk.Button(button_frame, text="Exit", command=exit_app)
        exit_button.pack(pady=5)
    def import_pgn(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Import PGN")
        tk.Label(dialog, text="Paste PGN text below:").pack(pady=5)
        self.pgn_text = tk.Text(dialog, height=10, width=50)
        self.pgn_text.pack(pady=5)
        tk.Button(dialog, text="Import", command=self.do_import_pgn).pack(pady=5)
    def do_import_pgn(self):
        pgn_str = self.pgn_text.get("1.0", tk.END).strip()
        try:
            game = chess.pgn.read_game(io.StringIO(pgn_str))
            if not game:
                raise ValueError("Invalid PGN")
            self.game = game
            self.move_list = list(game.mainline_moves())
            self.current_move = len(self.move_list) # start at end
            self.update_board_to_move(self.current_move)
            self.to_start_btn['state'] = tk.NORMAL
            self.back_btn['state'] = tk.NORMAL
            self.forward_btn['state'] = tk.NORMAL
            self.to_end_btn['state'] = tk.NORMAL
            white = game.headers.get("White", "White")
            black = game.headers.get("Black", "Black")
            date = game.headers.get("Date", "")
            event = game.headers.get("Event", "")
            self.game_name_var.set(f"{white} vs {black} {date} {event}")
            os.makedirs('pgn', exist_ok=True)
            filename = self.game_name_var.get().replace(" ", "_").replace("/", "_") + ".pgn"
            file_path = os.path.join('pgn', filename)
            with open(file_path, 'w') as f:
                f.write(pgn_str)
            self.pgn_text.master.destroy()
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Failed to import PGN: {str(e)}")
    def load_pgn(self):
        file_path = filedialog.askopenfilename(initialdir='pgn', filetypes=[('PGN files', '*.pgn')])
        if not file_path:
            return
        with open(file_path, 'r') as f:
            pgn_str = f.read()
        try:
            game = chess.pgn.read_game(io.StringIO(pgn_str))
            if not game:
                raise ValueError("Invalid PGN")
            self.game = game
            self.move_list = list(game.mainline_moves())
            self.current_move = len(self.move_list)
            self.update_board_to_move(self.current_move)
            self.to_start_btn['state'] = tk.NORMAL
            self.back_btn['state'] = tk.NORMAL
            self.forward_btn['state'] = tk.NORMAL
            self.to_end_btn['state'] = tk.NORMAL
            white = game.headers.get("White", "White")
            black = game.headers.get("Black", "Black")
            date = game.headers.get("Date", "")
            event = game.headers.get("Event", "")
            self.game_name_var.set(f"{white} vs {black} {date} {event}")
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Failed to load PGN: {str(e)}")
    def export_pgn(self):
        if not self.game:
            tkinter.messagebox.showerror("Error", "No game to export.")
            return
        file_path = filedialog.asksaveasfilename(initialdir='pgn', defaultextension=".pgn", filetypes=[('PGN files', '*.pgn')])
        if not file_path:
            return
        with open(file_path, 'w') as f:
            print(self.game, file=f, end="\n\n")
    def update_board_to_move(self, idx):
        self.save_state()
        self.current_move = idx
        board = self.game.board()
        for i in range(idx):
            board.push(self.move_list[i])
        self.board = board
        self.knights = []
        self.white_king_pos = None
        self.black_king_pos = None
        self.other_pieces = []
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                row = 7 - (square // 8)
                col = square % 8
                pos = [row, col]
                if piece.piece_type == chess.KNIGHT:
                    color = "white" if piece.color == chess.WHITE else "black"
                    self.knights.append({"pos": pos, "color": color, "selected": False})
                elif piece.piece_type == chess.KING:
                    if piece.color == chess.WHITE:
                        self.white_king_pos = pos
                    else:
                        self.black_king_pos = pos
                else:
                    self.other_pieces.append({"pos": pos, "type": piece.symbol()})
        self.legal_moves = []
        self.second_moves_groups = []
        self.right_click_pos = None
        self.right_click_second_pos = None
        self.right_click_third_pos = None
        self.right_click_fourth_pos = None
        self.right_click_second_moves = []
        self.right_click_third_moves = []
        self.right_click_fourth_moves = []
        self.show_move_numbers = False
        to_move = "White" if board.turn == chess.WHITE else "Black"
        self.to_move_var.set(f"{to_move} to move")
        self.draw_board()
        self.draw_coordinates()
        self.draw_pieces()
        self.draw_highlights()
    def to_start(self):
        if self.current_move > 0:
            self.update_board_to_move(0)
    def back(self):
        if self.current_move > 0:
            self.update_board_to_move(self.current_move - 1)
    def forward(self):
        if self.current_move < len(self.move_list):
            self.update_board_to_move(self.current_move + 1)
    def to_end(self):
        if self.current_move < len(self.move_list):
            self.update_board_to_move(len(self.move_list))
    # --- DRAG/DROP PIECE LOGIC ---
    def get_piece_at_pixel(self, x, y):
        """Return (piece_type, ref, pos) if a piece is under the pixel (x, y)."""
        col = (x - self.margin) // self.square_size
        row = (y - self.margin) // self.square_size
        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            return None, None, None
        pos = [row, col]
        for k in self.knights:
            if k["pos"] == pos:
                return "knight", k, pos
        if self.white_king_pos == pos:
            return "white_king", None, pos
        if self.black_king_pos == pos:
            return "black_king", None, pos
        for p in self.other_pieces:
            if p["pos"] == pos:
                return "piece", p, pos
        return None, None, None
    def on_piece_press(self, event):
        if self.add_piece_mode:
            return # Don't drag in Add Piece mode
        piece_type, piece_ref, pos = self.get_piece_at_pixel(event.x, event.y)
        if not piece_type:
            return
        self.drag_data["piece_type"] = piece_type
        self.drag_data["piece_ref"] = piece_ref
        self.drag_data["start_pos"] = pos
        self.drag_data["offset_x"] = event.x - (pos[1] * self.square_size + self.margin + self.square_size // 2)
        self.drag_data["offset_y"] = event.y - (pos[0] * self.square_size + self.margin + self.square_size // 2)
        # Draw a drag image (use correct icon)
        image = None
        if piece_type == "knight":
            if piece_ref["color"] == "white":
                image = self.white_knight_image
            else:
                image = self.black_knight_image
        elif piece_type == "white_king":
            image = self.white_king_image
        elif piece_type == "black_king":
            image = self.black_king_image
        elif piece_type == "piece":
            image = self.piece_images.get(piece_ref["type"])
        if image:
            self.drag_data["drag_image"] = self.canvas.create_image(
                event.x, event.y, image=image, tags="dragging", anchor=tk.CENTER
            )
        else:
            # fallback text
            text = "K" if piece_type == "white_king" else "k" if piece_type == "black_king" else piece_ref.get("type", "?")
            self.drag_data["drag_image"] = self.canvas.create_text(
                event.x, event.y, text=text, font=("Arial", 40), tags="dragging"
            )
        # Hide the piece from the board while dragging (so it doesn't appear at both old and new location)
        self.canvas.delete("pieces")
        self.draw_pieces_except_dragged()
    def draw_pieces_except_dragged(self):
        dragged_pos = self.drag_data.get("start_pos")
        dragged_type = self.drag_data.get("piece_type")
        dragged_ref = self.drag_data.get("piece_ref")
        for knight in self.knights:
            if dragged_type == "knight" and knight is dragged_ref:
                continue
            x, y = (knight["pos"][1] * self.square_size + self.margin + self.square_size // 2,
                    knight["pos"][0] * self.square_size + self.margin + self.square_size // 2)
            image = self.white_knight_image if knight["color"] == "white" else self.black_knight_image
            if image:
                self.canvas.create_image(x, y, image=image, tags="pieces")
            else:
                self.canvas.create_text(x, y, text="N" if knight["color"] == "white" else "n", font=("Arial", 40), tags="pieces")
        if self.white_king_pos and not (dragged_type == "white_king" and self.white_king_pos == dragged_pos):
            x, y = (self.white_king_pos[1] * self.square_size + self.margin + self.square_size // 2,
                    self.white_king_pos[0] * self.square_size + self.margin + self.square_size // 2)
            image = self.white_king_image
            if image:
                self.canvas.create_image(x, y, image=image, tags="pieces")
            else:
                self.canvas.create_text(x, y, text="K", font=("Arial", 40), tags="pieces")
        if self.black_king_pos and not (dragged_type == "black_king" and self.black_king_pos == dragged_pos):
            x, y = (self.black_king_pos[1] * self.square_size + self.margin + self.square_size // 2,
                    self.black_king_pos[0] * self.square_size + self.margin + self.square_size // 2)
            image = self.black_king_image
            if image:
                self.canvas.create_image(x, y, image=image, tags="pieces")
            else:
                self.canvas.create_text(x, y, text="k", font=("Arial", 40), tags="pieces")
        for piece in self.other_pieces:
            if dragged_type == "piece" and piece is dragged_ref:
                continue
            x, y = (piece["pos"][1] * self.square_size + self.margin + self.square_size // 2,
                    piece["pos"][0] * self.square_size + self.margin + self.square_size // 2)
            image = self.piece_images.get(piece["type"])
            if image:
                self.canvas.create_image(x, y, image=image, tags="pieces")
            else:
                self.canvas.create_text(x, y, text=piece["type"], font=("Arial", 40), tags="pieces")
    def on_piece_motion(self, event):
        if self.drag_data["drag_image"] is not None:
            self.canvas.coords(self.drag_data["drag_image"], event.x, event.y)
    def on_piece_release(self, event):
        if self.drag_data["drag_image"] is None:
            return
        col = (event.x - self.margin) // self.square_size
        row = (event.y - self.margin) // self.square_size
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            new_pos = [row, col]
            # If dropped on a new square or even on same, update piece position
            self.save_state()
            piece_type = self.drag_data["piece_type"]
            piece_ref = self.drag_data["piece_ref"]
            start_pos = self.drag_data["start_pos"]
            # --- FIX #1: Clear right-click analysis and highlights after drag ---
            self.legal_moves = []
            self.second_moves_groups = []
            self.right_click_pos = None
            self.right_click_second_pos = None
            self.right_click_third_pos = None
            self.right_click_fourth_pos = None
            self.right_click_second_moves = []
            self.right_click_third_moves = []
            self.right_click_fourth_moves = []
            self.show_move_numbers = False
            # --- FIX #2: Allow knights to capture opposite color pieces ---
            if piece_type == "knight":
                color = piece_ref["color"]
                # Remove any same color knight at new_pos (except the one we're moving)
                self.knights = [k for k in self.knights if k == piece_ref or k["pos"] != new_pos or k["color"] != color]
                # Remove any opposite color knight at the destination (capture)
                self.knights = [k for k in self.knights if k == piece_ref or k["pos"] != new_pos or k["color"] == color]
                # Remove opponent king if at new_pos (should never actually happen in real chess, but for this sandbox)
                if color == "white" and self.black_king_pos == new_pos:
                    self.black_king_pos = None
                if color == "black" and self.white_king_pos == new_pos:
                    self.white_king_pos = None
                # Remove opposite color other pieces at new_pos
                def is_opponent(piece):
                    if color == "white":
                        return piece["type"].islower()
                    else:
                        return piece["type"].isupper()
                self.other_pieces = [p for p in self.other_pieces if p["pos"] != new_pos or not is_opponent(p)]
                piece_ref["pos"] = new_pos
            elif piece_type == "white_king":
                # Remove black king if at new_pos
                if self.black_king_pos == new_pos:
                    self.black_king_pos = None
                # Remove black pieces at new_pos
                self.other_pieces = [p for p in self.other_pieces if p["pos"] != new_pos or not p["type"].islower()]
                self.knights = [k for k in self.knights if k["pos"] != new_pos or k["color"] == "white"]
                self.white_king_pos = new_pos
            elif piece_type == "black_king":
                if self.white_king_pos == new_pos:
                    self.white_king_pos = None
                self.other_pieces = [p for p in self.other_pieces if p["pos"] != new_pos or not p["type"].isupper()]
                self.knights = [k for k in self.knights if k["pos"] != new_pos or k["color"] == "black"]
                self.black_king_pos = new_pos
            elif piece_type == "piece":
                # Remove any piece at new_pos, then set piece_ref's pos
                self.other_pieces = [p for p in self.other_pieces if p == piece_ref or p["pos"] != new_pos]
                self.knights = [k for k in self.knights if k["pos"] != new_pos]
                if self.white_king_pos == new_pos:
                    self.white_king_pos = None
                if self.black_king_pos == new_pos:
                    self.black_king_pos = None
                piece_ref["pos"] = new_pos
            # Remove any duplicate piece at destination
            self.knights = [k for i, k in enumerate(self.knights) if k not in self.knights[:i]]
            self.other_pieces = [p for i, p in enumerate(self.other_pieces) if p not in self.other_pieces[:i]]
        # Remove drag image and redraw everything
        if self.drag_data["drag_image"]:
            self.canvas.delete(self.drag_data["drag_image"])
        self.drag_data = {"piece_type": None, "piece_ref": None, "start_pos": None, "drag_image": None, "offset_x": 0, "offset_y": 0}
        self.draw_board()
        self.draw_coordinates()
        self.draw_pieces()
        self.draw_highlights()
       
    def swap_board_colors(self):
        self.use_green_theme = not self.use_green_theme
        if self.use_green_theme:
            self.light_color = self.light_color_green
            self.dark_color = self.dark_color_green
        else:
            self.light_color = self.light_color_default
            self.dark_color = self.dark_color_default
        self.save_colors()
        self.draw_board()
        self.draw_coordinates()
        self.draw_pieces()
        self.draw_highlights()
    def draw_board(self):
        self.canvas.delete("board")
        for row in range(self.board_size):
            for col in range(self.board_size):
                color = self.light_color if (row + col) % 2 == 0 else self.dark_color
                x1, y1 = col * self.square_size + self.margin, row * self.square_size + self.margin
                x2, y2 = x1 + self.square_size, y1 + self.square_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, tags="board")
    def draw_coordinates(self):
        self.canvas.delete("coordinates")
        for row in range(self.board_size):
            rank = 8 - row
            y = row * self.square_size + self.margin + self.square_size // 2
            self.canvas.create_text(self.margin // 2, y, text=str(rank), font=("Arial", 12), tags="coordinates")
            self.canvas.create_text(self.margin + self.board_size * self.square_size + self.margin // 2, y,
                                    text=str(rank), font=("Arial", 12), tags="coordinates")
        for col in range(self.board_size):
            file_letter = chr(97 + col)
            x = col * self.square_size + self.margin + self.square_size // 2
            self.canvas.create_text(x, self.margin // 2, text=file_letter, font=("Arial", 12), tags="coordinates")
            self.canvas.create_text(x, self.margin + self.board_size * self.square_size + self.margin // 2,
                                    text=file_letter, font=("Arial", 12), tags="coordinates")
    def draw_pieces(self):
        self.canvas.delete("pieces")
        for knight in self.knights:
            x, y = (knight["pos"][1] * self.square_size + self.margin + self.square_size // 2,
                    knight["pos"][0] * self.square_size + self.margin + self.square_size // 2)
            if knight["color"] == "white":
                image = self.white_knight_image or self.canvas.create_text(x, y, text="N", font=("Arial", 40))
                if self.white_knight_image:
                    self.canvas.create_image(x, y, image=image, tags="pieces")
            else:
                image = self.black_knight_image or self.canvas.create_text(x, y, text="n", font=("Arial", 40))
                if self.black_knight_image:
                    self.canvas.create_image(x, y, image=image, tags="pieces")
        if self.white_king_pos:
            x, y = (self.white_king_pos[1] * self.square_size + self.margin + self.square_size // 2,
                    self.white_king_pos[0] * self.square_size + self.margin + self.square_size // 2)
            image = self.white_king_image or self.canvas.create_text(x, y, text="K", font=("Arial", 40))
            if self.white_king_image:
                self.canvas.create_image(x, y, image=image, tags="pieces")
        if self.black_king_pos:
            x, y = (self.black_king_pos[1] * self.square_size + self.margin + self.square_size // 2,
                    self.black_king_pos[0] * self.square_size + self.margin + self.square_size // 2)
            image = self.black_king_image or self.canvas.create_text(x, y, text="k", font=("Arial", 40))
            if self.black_king_image:
                self.canvas.create_image(x, y, image=image, tags="pieces")
        for piece in self.other_pieces:
            x, y = (piece["pos"][1] * self.square_size + self.margin + self.square_size // 2,
                    piece["pos"][0] * self.square_size + self.margin + self.square_size // 2)
            image = self.piece_images.get(piece["type"])
            if image:
                self.canvas.create_image(x, y, image=image, tags="pieces")
            else:
                self.canvas.create_text(x, y, text=piece["type"], font=("Arial", 40), tags="pieces")
    # --- UPDATED draw_highlights for overlapping legal moves and multi-labeling ---
    def show_first_and_second_moves(self):
        self.save_state()
        # Clear all highlights, keep only for the selected knight
        for knight in self.knights:
            if knight["selected"]:
                # 1st moves from the selected knight
                self.legal_moves = self.get_knight_legal_moves(knight["pos"], knight["color"])
                self.second_moves_groups = []
                self.right_click_pos = None
                self.right_click_second_pos = None
                self.right_click_third_pos = None
                self.right_click_fourth_pos = None
                self.right_click_second_moves = []
                self.right_click_third_moves = []
                self.right_click_fourth_moves = []
                self.show_move_numbers = False
                # For each possible 1st move, compute all possible 2nd moves (excluding jumping back to starting square)
                knight_start = knight["pos"]
                for idx, move in enumerate(self.legal_moves):
                    # Second moves from this 1st move, for this knight
                    second_moves = self.get_knight_legal_moves(move, knight["color"])
                    # Remove the square the knight started from, so 2nd move can't go back to original
                    filtered_second_moves = [sm for sm in second_moves if sm != knight_start]
                    self.second_moves_groups.append(filtered_second_moves)
                break
        self.draw_board()
        self.draw_coordinates()
        self.draw_pieces()
        self.draw_highlights()
    def draw_highlights(self):
        self.canvas.delete("highlight")
        small_size = self.square_size * 0.2
        offset = (self.square_size - small_size) / 2
        def draw_label(x, y, nums):
            if isinstance(nums, (list, tuple)):
                nums = sorted(set(nums))
                txt = ",".join(str(n) for n in nums)
            else:
                txt = str(nums)
            self.canvas.create_text(x, y, text=txt, font=("Arial", 10, "bold"), tags="highlight")
        # Show step move squares with label logic for jump-back
        if self.right_click_pos is not None:
            x1, y1 = self.right_click_pos[1] * self.square_size + self.margin + offset, self.right_click_pos[0] * self.square_size + self.margin + offset
            x2, y2 = x1 + small_size, y1 + small_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.first_move_color, tags="highlight")
            show_13 = (
                self.right_click_third_pos is not None and
                self.right_click_pos == self.right_click_third_pos and
                (self.right_click_second_pos is None or self.right_click_second_pos != self.right_click_pos)
            )
            nums = [1, 3] if show_13 else [1]
            draw_label(x1 + small_size + 18, y1 + small_size // 2, nums)
        if self.right_click_second_pos is not None:
            x1, y1 = self.right_click_second_pos[1] * self.square_size + self.margin + offset, self.right_click_second_pos[0] * self.square_size + self.margin + offset
            x2, y2 = x1 + small_size, y1 + small_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.right_click_color, tags="highlight")
            show_24 = (
                self.right_click_fourth_pos is not None and
                self.right_click_second_pos == self.right_click_fourth_pos and
                (self.right_click_third_pos is None or self.right_click_third_pos != self.right_click_second_pos)
            )
            nums = [2, 4] if show_24 else [2]
            draw_label(x1 + small_size + 18, y1 + small_size // 2, nums)
        if self.right_click_third_pos is not None:
            label_this = not (
                self.right_click_pos is not None and
                self.right_click_third_pos == self.right_click_pos and
                (self.right_click_second_pos is None or self.right_click_second_pos != self.right_click_pos)
            )
            if label_this:
                x1, y1 = self.right_click_third_pos[1] * self.square_size + self.margin + offset, self.right_click_third_pos[0] * self.square_size + self.margin + offset
                x2, y2 = x1 + small_size, y1 + small_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.third_move_color, tags="highlight")
                draw_label(x1 + small_size + 18, y1 + small_size // 2, 3)
        if self.right_click_fourth_pos is not None:
            label_this = not (
                self.right_click_second_pos is not None and
                self.right_click_fourth_pos == self.right_click_second_pos and
                (self.right_click_third_pos is None or self.right_click_third_pos != self.right_click_second_pos)
            )
            if label_this:
                x1, y1 = self.right_click_fourth_pos[1] * self.square_size + self.margin + offset, self.right_click_fourth_pos[0] * self.square_size + self.margin + offset
                x2, y2 = x1 + small_size, y1 + small_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.fourth_move_color, tags="highlight")
                draw_label(x1 + small_size + 18, y1 + small_size // 2, 4)
        # Show 1st/2nd move analysis if present (from show_first_and_second_moves)
        if self.legal_moves and not self.right_click_fourth_pos:
            for move in self.legal_moves:
                x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                x2, y2 = x1 + small_size, y1 + small_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.first_move_color, tags="highlight")
        if self.second_moves_groups:
            for idx, group in enumerate(self.second_moves_groups):
                color = self.second_move_colors[idx % len(self.second_move_colors)]
                for move in group:
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, tags="highlight")
        # Show current layer of possible moves for right-click analysis, ONLY if not finished (not after 4th move)
        selected_knight = next((knight for knight in self.knights if knight["selected"]), None)
        if selected_knight and not self.right_click_fourth_pos:
            if self.right_click_pos is None:
                for move in self.get_knight_legal_moves(selected_knight["pos"], selected_knight["color"]):
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.first_move_color, tags="highlight")
            elif self.right_click_pos is not None and self.right_click_second_pos is None:
                for move in self.get_knight_legal_moves(selected_knight["pos"], selected_knight["color"]):
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.first_move_color, tags="highlight")
                for move in self.right_click_second_moves:
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.right_click_color, tags="highlight")
            elif self.right_click_second_pos is not None and self.right_click_third_pos is None:
                for move in self.get_knight_legal_moves(selected_knight["pos"], selected_knight["color"]):
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.first_move_color, tags="highlight")
                for move in self.right_click_second_moves:
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.right_click_color, tags="highlight")
                for move in self.right_click_third_moves:
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.third_move_color, tags="highlight")
            elif self.right_click_third_pos is not None and self.right_click_fourth_pos is None:
                for move in self.get_knight_legal_moves(selected_knight["pos"], selected_knight["color"]):
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.first_move_color, tags="highlight")
                for move in self.right_click_second_moves:
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.right_click_color, tags="highlight")
                for move in self.right_click_third_moves:
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.third_move_color, tags="highlight")
                for move in self.right_click_fourth_moves:
                    x1, y1 = move[1] * self.square_size + self.margin + offset, move[0] * self.square_size + self.margin + offset
                    x2, y2 = x1 + small_size, y1 + small_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.fourth_move_color, tags="highlight")
    # --- Knight analysis logic ---
    def on_right_click(self, event):
        col = (event.x - self.margin) // self.square_size
        row = (event.y - self.margin) // self.square_size
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            clicked_pos = [row, col]
            selected_knight = next((knight for knight in self.knights if knight["selected"]), None)
            if selected_knight:
                # Step 1: select first gold
                if self.right_click_pos is None and clicked_pos in self.get_knight_legal_moves(selected_knight["pos"], selected_knight["color"]):
                    self.save_state()
                    self.right_click_pos = clicked_pos
                    self.right_click_second_pos = None
                    self.right_click_third_pos = None
                    self.right_click_fourth_pos = None
                    self.right_click_second_moves = self.get_knight_legal_moves(clicked_pos, selected_knight["color"])
                    self.right_click_third_moves = []
                    self.right_click_fourth_moves = []
                    self.show_move_numbers = True
                # Step 2: select pink
                elif self.right_click_pos and self.right_click_second_pos is None and clicked_pos in self.right_click_second_moves:
                    self.save_state()
                    self.right_click_second_pos = clicked_pos
                    self.right_click_third_pos = None
                    self.right_click_fourth_pos = None
                    self.right_click_third_moves = self.get_knight_legal_moves(clicked_pos, selected_knight["color"])
                    self.right_click_fourth_moves = []
                    self.show_move_numbers = True
                # Step 3: select light blue
                elif self.right_click_second_pos and self.right_click_third_pos is None and clicked_pos in self.right_click_third_moves:
                    self.save_state()
                    self.right_click_third_pos = clicked_pos
                    self.right_click_fourth_pos = None
                    self.right_click_fourth_moves = self.get_knight_legal_moves(clicked_pos, selected_knight["color"])
                    self.show_move_numbers = True
                # Step 4: select fourth
                elif self.right_click_third_pos and self.right_click_fourth_pos is None and clicked_pos in self.right_click_fourth_moves:
                    self.save_state()
                    self.right_click_fourth_pos = clicked_pos
                    self.right_click_second_moves = []
                    self.right_click_third_moves = []
                    self.right_click_fourth_moves = []
                    self.show_move_numbers = True
                # Back from 2 to 1
                elif self.right_click_pos and self.right_click_second_pos and clicked_pos == self.right_click_pos:
                    self.save_state()
                    self.right_click_second_pos = None
                    self.right_click_third_pos = None
                    self.right_click_fourth_pos = None
                    self.right_click_second_moves = self.get_knight_legal_moves(clicked_pos, selected_knight["color"])
                    self.right_click_third_moves = []
                    self.right_click_fourth_moves = []
                    self.show_move_numbers = True
                # Back from 3 to 2
                elif self.right_click_second_pos and self.right_click_third_pos and clicked_pos == self.right_click_second_pos:
                    self.save_state()
                    self.right_click_third_pos = None
                    self.right_click_fourth_pos = None
                    self.right_click_third_moves = self.get_knight_legal_moves(clicked_pos, selected_knight["color"])
                    self.right_click_fourth_moves = []
                    self.show_move_numbers = True
                else:
                    self.save_state()
                    self.right_click_pos = None
                    self.right_click_second_pos = None
                    self.right_click_third_pos = None
                    self.right_click_fourth_pos = None
                    self.right_click_second_moves = []
                    self.right_click_third_moves = []
                    self.right_click_fourth_moves = []
                    self.show_move_numbers = False
        else:
            self.save_state()
            self.right_click_pos = None
            self.right_click_second_pos = None
            self.right_click_third_pos = None
            self.right_click_fourth_pos = None
            self.right_click_second_moves = []
            self.right_click_third_moves = []
            self.right_click_fourth_moves = []
            self.show_move_numbers = False
        self.draw_board()
        self.draw_coordinates()
        self.draw_pieces()
        self.draw_highlights()
    # --- All remaining unchanged methods from previous completions ---
    # get_piece_at, get_knight_legal_moves, get_legal_moves, save_state, undo, redo, on_left_click,
    # show_first_and_second_moves, toggle_add_piece_mode, select_add_piece, do_add_piece, reset,
    # add_random_game, new_standard_game
    def get_piece_at(self, pos):
        for k in self.knights:
            if k["pos"] == pos:
                return k
        for p in self.other_pieces:
            if p["pos"] == pos:
                return p
        if self.white_king_pos and self.white_king_pos == pos:
            return {"type": "K", "pos": pos}
        if self.black_king_pos and self.black_king_pos == pos:
            return {"type": "k", "pos": pos}
        return None
    def get_knight_legal_moves(self, pos, knight_color):
        moves = []
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        blocked = []
        if self.white_king_pos:
            blocked.append(self.white_king_pos)
        if self.black_king_pos:
            blocked.append(self.black_king_pos)
        same_color_knights = [k["pos"] for k in self.knights if k["color"] == knight_color and k["pos"] != pos]
        blocked.extend(same_color_knights)
        for op in self.other_pieces:
            if (knight_color == "white" and op["type"].isupper()) or (knight_color == "black" and op["type"].islower()):
                blocked.append(op["pos"])
        for dr, dc in knight_moves:
            r, c = pos[0] + dr, pos[1] + dc
            if 0 <= r < self.board_size and 0 <= c < self.board_size and [r, c] not in blocked:
                moves.append([r, c])
        return moves
    def get_legal_moves(self, pos, piece_type_or_color):
        piece = self.get_piece_at(pos)
        if not piece:
            return []
        piece_type = piece.get("type", None)
        if (piece_type is None and "color" in piece) or (piece_type and piece_type.lower() == "n"):
            return self.get_knight_legal_moves(pos, piece.get("color", "white"))
        moves = []
        board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        for k in self.knights:
            board[k["pos"][0]][k["pos"][1]] = "N" if k["color"] == "white" else "n"
        for op in self.other_pieces:
            board[op["pos"][0]][op["pos"][1]] = op["type"]
        if self.white_king_pos:
            board[self.white_king_pos[0]][self.white_king_pos[1]] = "K"
        if self.black_king_pos:
            board[self.black_king_pos[0]][self.black_king_pos[1]] = "k"
        r0, c0 = pos
        color_is_white = (piece_type.isupper()) if piece_type else True
        if piece_type in ['P', 'p']:
            direction = -1 if color_is_white else 1
            start_row = 6 if color_is_white else 1
            if 0 <= r0+direction < self.board_size and board[r0+direction][c0] is None:
                moves.append([r0+direction, c0])
                if r0 == start_row and board[r0+2*direction][c0] is None:
                    moves.append([r0+2*direction, c0])
            for dc in [-1, 1]:
                c1 = c0+dc
                r1 = r0+direction
                if 0 <= c1 < self.board_size and 0 <= r1 < self.board_size:
                    target = board[r1][c1]
                    if target and ((color_is_white and target.islower()) or (not color_is_white and target.isupper())):
                        moves.append([r1, c1])
        elif piece_type in ['R', 'r']:
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                for step in range(1,8):
                    r, c = r0 + dr*step, c0 + dc*step
                    if 0<=r<8 and 0<=c<8:
                        target = board[r][c]
                        if not target:
                            moves.append([r,c])
                        else:
                            if (color_is_white and target.islower()) or (not color_is_white and target.isupper()):
                                moves.append([r,c])
                            break
                    else:
                        break
        elif piece_type in ['B', 'b']:
            for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                for step in range(1,8):
                    r, c = r0 + dr*step, c0 + dc*step
                    if 0<=r<8 and 0<=c<8:
                        target = board[r][c]
                        if not target:
                            moves.append([r,c])
                        else:
                            if (color_is_white and target.islower()) or (not color_is_white and target.isupper()):
                                moves.append([r,c])
                            break
                    else:
                        break
        elif piece_type in ['Q', 'q']:
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                for step in range(1,8):
                    r, c = r0 + dr*step, c0 + dc*step
                    if 0<=r<8 and 0<=c<8:
                        target = board[r][c]
                        if not target:
                            moves.append([r,c])
                        else:
                            if (color_is_white and target.islower()) or (not color_is_white and target.isupper()):
                                moves.append([r,c])
                            break
                    else:
                        break
        return moves
    def save_state(self):
        state = {
            "knights": [knight.copy() for knight in self.knights],
            "white_king_pos": self.white_king_pos[:] if self.white_king_pos else None,
            "black_king_pos": self.black_king_pos[:] if self.black_king_pos else None,
            "white_king_selected": self.white_king_selected,
            "black_king_selected": self.black_king_selected,
            "legal_moves": self.legal_moves[:],
            "second_moves_groups": [group[:] for group in self.second_moves_groups],
            "right_click_pos": self.right_click_pos,
            "right_click_second_pos": self.right_click_second_pos,
            "right_click_third_pos": self.right_click_third_pos,
            "right_click_fourth_pos": self.right_click_fourth_pos,
            "right_click_second_moves": self.right_click_second_moves[:],
            "right_click_third_moves": self.right_click_third_moves[:],
            "right_click_fourth_moves": self.right_click_fourth_moves[:],
            "show_move_numbers": self.show_move_numbers,
            "other_pieces": [piece.copy() for piece in self.other_pieces],
            "board_fen": self.board.fen() if self.board else None,
            "current_coord": self.current_coord.get() if hasattr(self, "current_coord") else "Selected: None",
        }
        self.history.append(state)
        self.redo_stack.clear()
    def undo(self):
        if self.history:
            state = self.history.pop()
            redo_state = {
                "knights": [knight.copy() for knight in self.knights],
                "white_king_pos": self.white_king_pos[:] if self.white_king_pos else None,
                "black_king_pos": self.black_king_pos[:] if self.black_king_pos else None,
                "white_king_selected": self.white_king_selected,
                "black_king_selected": self.black_king_selected,
                "legal_moves": self.legal_moves[:],
                "second_moves_groups": [group[:] for group in self.second_moves_groups],
                "right_click_pos": self.right_click_pos,
                "right_click_second_pos": self.right_click_second_pos,
                "right_click_third_pos": self.right_click_third_pos,
                "right_click_fourth_pos": self.right_click_fourth_pos,
                "right_click_second_moves": self.right_click_second_moves[:],
                "right_click_third_moves": self.right_click_third_moves[:],
                "right_click_fourth_moves": self.right_click_fourth_moves[:],
                "show_move_numbers": self.show_move_numbers,
                "other_pieces": [piece.copy() for piece in self.other_pieces],
                "board_fen": self.board.fen() if self.board else None,
                "current_coord": self.current_coord.get() if hasattr(self, "current_coord") else "Selected: None",
            }
            self.redo_stack.append(redo_state)
            self.knights = [knight.copy() for knight in state["knights"]]
            self.white_king_pos = state["white_king_pos"][:] if state["white_king_pos"] else None
            self.black_king_pos = state["black_king_pos"][:] if state["black_king_pos"] else None
            self.white_king_selected = state["white_king_selected"]
            self.black_king_selected = state["black_king_selected"]
            self.legal_moves = state["legal_moves"][:]
            self.second_moves_groups = [group[:] for group in state["second_moves_groups"]]
            self.right_click_pos = state["right_click_pos"]
            self.right_click_second_pos = state["right_click_second_pos"]
            self.right_click_third_pos = state["right_click_third_pos"]
            self.right_click_fourth_pos = state["right_click_fourth_pos"]
            self.right_click_second_moves = state["right_click_second_moves"][:]
            self.right_click_third_moves = state["right_click_third_moves"][:]
            self.right_click_fourth_moves = state["right_click_fourth_moves"][:]
            self.show_move_numbers = state["show_move_numbers"]
            self.other_pieces = [piece.copy() for piece in state["other_pieces"]]
            if state["board_fen"]:
                self.board.set_fen(state["board_fen"])
            else:
                self.board = chess.Board()
            if hasattr(self, "current_coord"):
                self.current_coord.set(state.get("current_coord", "Selected: None"))
            self.draw_board()
            self.draw_coordinates()
            self.draw_pieces()
            self.draw_highlights()
    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            undo_state = {
                "knights": [knight.copy() for knight in self.knights],
                "white_king_pos": self.white_king_pos[:] if self.white_king_pos else None,
                "black_king_pos": self.black_king_pos[:] if self.black_king_pos else None,
                "white_king_selected": self.white_king_selected,
                "black_king_selected": self.black_king_selected,
                "legal_moves": self.legal_moves[:],
                "second_moves_groups": [group[:] for group in self.second_moves_groups],
                "right_click_pos": self.right_click_pos,
                "right_click_second_pos": self.right_click_second_pos,
                "right_click_third_pos": self.right_click_third_pos,
                "right_click_fourth_pos": self.right_click_fourth_pos,
                "right_click_second_moves": self.right_click_second_moves[:],
                "right_click_third_moves": self.right_click_third_moves[:],
                "right_click_fourth_moves": self.right_click_fourth_moves[:],
                "show_move_numbers": self.show_move_numbers,
                "other_pieces": [piece.copy() for piece in self.other_pieces],
                "board_fen": self.board.fen() if self.board else None,
                "current_coord": self.current_coord.get() if hasattr(self, "current_coord") else "Selected: None",
            }
            self.history.append(undo_state)
            self.knights = [knight.copy() for knight in state["knights"]]
            self.white_king_pos = state["white_king_pos"][:] if state["white_king_pos"] else None
            self.black_king_pos = state["black_king_pos"][:] if state["black_king_pos"] else None
            self.white_king_selected = state["white_king_selected"]
            self.black_king_selected = state["black_king_selected"]
            self.legal_moves = state["legal_moves"][:]
            self.second_moves_groups = [group[:] for group in state["second_moves_groups"]]
            self.right_click_pos = state["right_click_pos"]
            self.right_click_second_pos = state["right_click_second_pos"]
            self.right_click_third_pos = state["right_click_third_pos"]
            self.right_click_fourth_pos = state["right_click_fourth_pos"]
            self.right_click_second_moves = state["right_click_second_moves"][:]
            self.right_click_third_moves = state["right_click_third_moves"][:]
            self.right_click_fourth_moves = state["right_click_fourth_moves"][:]
            self.show_move_numbers = state["show_move_numbers"]
            self.other_pieces = [piece.copy() for piece in state["other_pieces"]]
            if state["board_fen"]:
                self.board.set_fen(state["board_fen"])
            else:
                self.board = chess.Board()
            if hasattr(self, "current_coord"):
                self.current_coord.set(state.get("current_coord", "Selected: None"))
            self.draw_board()
            self.draw_coordinates()
            self.draw_pieces()
            self.draw_highlights()
    def on_left_click(self, event):
        col = (event.x - self.margin) // self.square_size
        row = (event.y - self.margin) // self.square_size
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            clicked_pos = [row, col]
            coord_text = f"Selected: {chr(97+col)}{8-row}"
            self.current_coord.set(coord_text)
            if self.add_piece_mode:
                if self.add_piece_selected:
                    self.do_add_piece(clicked_pos, self.add_piece_selected)
                    self.add_piece_mode = False
                    self.add_piece_btn.config(relief=tk.RAISED)
                    self.add_piece_selected = None
                    self.add_piece_square = None
                    self.draw_board()
                    self.draw_coordinates()
                    self.draw_pieces()
                    self.draw_highlights()
                    return
                else:
                    self.add_piece_square = clicked_pos
                    return
            if self.add_piece_selected and self.add_piece_square is not None:
                self.do_add_piece(clicked_pos, self.add_piece_selected)
                self.add_piece_mode = False
                self.add_piece_btn.config(relief=tk.RAISED)
                self.add_piece_selected = None
                self.add_piece_square = None
                self.draw_board()
                self.draw_coordinates()
                self.draw_pieces()
                self.draw_highlights()
                return
            selected_knight = next((k for k in self.knights if k["selected"]), None)
            selected_piece = next((p for p in self.other_pieces if p.get("selected", False)), None)
            if selected_knight and clicked_pos in self.get_knight_legal_moves(selected_knight["pos"], selected_knight["color"]):
                self.save_state()
                self.knights = [k for k in self.knights if k["pos"] != clicked_pos or k["color"] == selected_knight["color"] or k["selected"]]
                self.other_pieces = [p for p in self.other_pieces if p["pos"] != clicked_pos or
                                     (selected_knight["color"] == "white" and p["type"].isupper()) or
                                     (selected_knight["color"] == "black" and p["type"].islower())]
                selected_knight["pos"] = clicked_pos
                self.legal_moves = []
                self.second_moves_groups = []
                self.right_click_pos = None
                self.right_click_second_pos = None
                self.right_click_third_pos = None
                self.right_click_fourth_pos = None
                self.right_click_second_moves = []
                self.right_click_third_moves = []
                self.right_click_fourth_moves = []
                self.show_move_numbers = False
                for k in self.knights:
                    k["selected"] = False
            elif selected_piece and clicked_pos in self.get_legal_moves(selected_piece["pos"], selected_piece["type"]):
                self.save_state()
                piece_type = selected_piece["type"]
                color_is_white = piece_type.isupper()
                self.other_pieces = [p for p in self.other_pieces if p is selected_piece or p["pos"] != clicked_pos or
                                     (color_is_white and p["type"].isupper()) or (not color_is_white and p["type"].islower())]
                self.knights = [k for k in self.knights if k["pos"] != clicked_pos or
                                (color_is_white and k["color"]=="white") or (not color_is_white and k["color"]=="black")]
                selected_piece["pos"] = clicked_pos
                selected_piece["selected"] = False
                self.legal_moves = []
                self.second_moves_groups = []
                self.right_click_pos = None
                self.right_click_second_pos = None
                self.right_click_third_pos = None
                self.right_click_fourth_pos = None
                self.right_click_second_moves = []
                self.right_click_third_moves = []
                self.right_click_fourth_moves = []
                self.show_move_numbers = False
            elif self.white_king_selected and self.white_king_pos:
                white_knight_positions = [k["pos"] for k in self.knights if k["color"] == "white"]
                white_other_positions = [p["pos"] for p in self.other_pieces if p["type"].isupper()]
                blocked = white_knight_positions + white_other_positions
                if self.black_king_pos:
                    blocked.append(self.black_king_pos)
                if clicked_pos not in blocked:
                    self.save_state()
                    self.knights = [k for k in self.knights if k["pos"] != clicked_pos or k["color"] != "black"]
                    self.other_pieces = [p for p in self.other_pieces if p["pos"] != clicked_pos or p["type"].isupper()]
                    self.white_king_pos = clicked_pos
                    self.white_king_selected = False
                    self.legal_moves = []
                    self.second_moves_groups = []
                    self.right_click_pos = None
                    self.right_click_second_pos = None
                    self.right_click_third_pos = None
                    self.right_click_fourth_pos = None
                    self.right_click_second_moves = []
                    self.right_click_third_moves = []
                    self.right_click_fourth_moves = []
                    self.show_move_numbers = False
                else:
                    self.save_state()
                    self.white_king_selected = False
                    self.legal_moves = []
                    self.second_moves_groups = []
                    self.right_click_pos = None
                    self.right_click_second_pos = None
                    self.right_click_third_pos = None
                    self.right_click_fourth_pos = None
                    self.right_click_second_moves = []
                    self.right_click_third_moves = []
                    self.right_click_fourth_moves = []
                    self.show_move_numbers = False
            elif self.black_king_selected and self.black_king_pos:
                black_knight_positions = [k["pos"] for k in self.knights if k["color"] == "black"]
                black_other_positions = [p["pos"] for p in self.other_pieces if p["type"].islower()]
                blocked = black_knight_positions + black_other_positions
                if self.white_king_pos:
                    blocked.append(self.white_king_pos)
                if clicked_pos not in blocked:
                    self.save_state()
                    self.knights = [k for k in self.knights if k["pos"] != clicked_pos or k["color"] != "white"]
                    self.other_pieces = [p for p in self.other_pieces if p["pos"] != clicked_pos or p["type"].islower()]
                    self.black_king_pos = clicked_pos
                    self.black_king_selected = False
                    self.legal_moves = []
                    self.second_moves_groups = []
                    self.right_click_pos = None
                    self.right_click_second_pos = None
                    self.right_click_third_pos = None
                    self.right_click_fourth_pos = None
                    self.right_click_second_moves = []
                    self.right_click_third_moves = []
                    self.right_click_fourth_moves = []
                    self.show_move_numbers = False
                else:
                    self.save_state()
                    self.black_king_selected = False
                    self.legal_moves = []
                    self.second_moves_groups = []
                    self.right_click_pos = None
                    self.right_click_second_pos = None
                    self.right_click_third_pos = None
                    self.right_click_fourth_pos = None
                    self.right_click_second_moves = []
                    self.right_click_third_moves = []
                    self.right_click_fourth_moves = []
                    self.show_move_numbers = False
            else:
                self.save_state()
                for knight in self.knights:
                    knight["selected"] = False
                for p in self.other_pieces:
                    p["selected"] = False
                self.white_king_selected = False
                self.black_king_selected = False
                self.legal_moves = []
                for knight in self.knights:
                    if clicked_pos == knight["pos"]:
                        knight["selected"] = True
                        self.legal_moves = self.get_knight_legal_moves(knight["pos"], knight["color"])
                        self.second_moves_groups = []
                        self.right_click_pos = None
                        self.right_click_second_pos = None
                        self.right_click_third_pos = None
                        self.right_click_fourth_pos = None
                        self.right_click_second_moves = []
                        self.right_click_third_moves = []
                        self.right_click_fourth_moves = []
                        self.show_move_numbers = False
                        break
                else:
                    for p in self.other_pieces:
                        if clicked_pos == p["pos"]:
                            p["selected"] = True
                            self.legal_moves = self.get_legal_moves(p["pos"], p["type"])
                            self.second_moves_groups = []
                            self.right_click_pos = None
                            self.right_click_second_pos = None
                            self.right_click_third_pos = None
                            self.right_click_fourth_pos = None
                            self.right_click_second_moves = []
                            self.right_click_third_moves = []
                            self.right_click_fourth_moves = []
                            self.show_move_numbers = False
                            break
                    else:
                        if self.white_king_pos and clicked_pos == self.white_king_pos:
                            self.white_king_selected = True
                        elif self.black_king_pos and clicked_pos == self.black_king_pos:
                            self.black_king_selected = True
                        else:
                            self.second_moves_groups = []
                            self.right_click_pos = None
                            self.right_click_second_pos = None
                            self.right_click_third_pos = None
                            self.right_click_fourth_pos = None
                            self.right_click_second_moves = []
                            self.right_click_third_moves = []
                            self.right_click_fourth_moves = []
                            self.show_move_numbers = False
        else:
            self.current_coord.set("Selected: None")
            self.save_state()
            for knight in self.knights:
                knight["selected"] = False
            for p in self.other_pieces:
                p["selected"] = False
            self.white_king_selected = False
            self.black_king_selected = False
            self.legal_moves = []
            self.second_moves_groups = []
            self.right_click_pos = None
            self.right_click_second_pos = None
            self.right_click_third_pos = None
            self.right_click_fourth_pos = None
            self.right_click_second_moves = []
            self.right_click_third_moves = []
            self.right_click_fourth_moves = []
            self.show_move_numbers = False
        self.draw_board()
        self.draw_coordinates()
        self.draw_pieces()
        self.draw_highlights()
   
    def toggle_add_piece_mode(self):
        self.add_piece_mode = not self.add_piece_mode
        if self.add_piece_mode:
            self.add_piece_btn.config(relief=tk.SUNKEN)
        else:
            self.add_piece_btn.config(relief=tk.RAISED)
        self.add_piece_selected = None
        self.add_piece_square = None
    def select_add_piece(self, piece_type):
        self.add_piece_selected = piece_type
        self.add_piece_mode = True
        self.add_piece_btn.config(relief=tk.SUNKEN)
        if self.add_piece_square is not None:
            self.do_add_piece(self.add_piece_square, self.add_piece_selected)
            self.add_piece_mode = False
            self.add_piece_btn.config(relief=tk.RAISED)
            self.add_piece_selected = None
            self.add_piece_square = None
            self.draw_board()
            self.draw_coordinates()
            self.draw_pieces()
            self.draw_highlights()
    def do_add_piece(self, pos, piece_type):
        self.save_state()
        self.knights = [k for k in self.knights if k["pos"] != pos]
        self.other_pieces = [p for p in self.other_pieces if p["pos"] != pos]
        if self.white_king_pos and self.white_king_pos == pos:
            self.white_king_pos = None
        if self.black_king_pos and self.black_king_pos == pos:
            self.black_king_pos = None
        if piece_type == 'N':
            self.knights.append({"pos": pos, "color": "white", "selected": False})
        elif piece_type == 'n':
            self.knights.append({"pos": pos, "color": "black", "selected": False})
        elif piece_type == 'K':
            self.white_king_pos = pos
        elif piece_type == 'k':
            self.black_king_pos = pos
        else:
            self.other_pieces.append({"pos": pos, "type": piece_type})
        self.legal_moves = []
        self.second_moves_groups = []
        self.right_click_pos = None
        self.right_click_second_pos = None
        self.right_click_third_pos = None
        self.right_click_fourth_pos = None
        self.right_click_second_moves = []
        self.right_click_third_moves = []
        self.right_click_fourth_moves = []
        self.show_move_numbers = False
    def reset(self):
        if self.last_random_game_set:
            if self.last_random_game_state:
                state = self.last_random_game_state
                self.knights = [knight.copy() for knight in state["knights"]]
                self.white_king_pos = state["white_king_pos"][:] if state["white_king_pos"] else None
                self.black_king_pos = state["black_king_pos"][:] if state["black_king_pos"] else None
                self.white_king_selected = False
                self.black_king_selected = False
                self.legal_moves = []
                self.second_moves_groups = []
                self.right_click_pos = None
                self.right_click_second_pos = None
                self.right_click_third_pos = None
                self.right_click_fourth_pos = None
                self.right_click_second_moves = []
                self.right_click_third_moves = []
                self.right_click_fourth_moves = []
                self.show_move_numbers = False
                self.other_pieces = [piece.copy() for piece in state["other_pieces"]]
                self.board = chess.Board()
                if state["board_fen"]:
                    self.board.set_fen(state["board_fen"])
                self.last_random_game_set = False
                self.draw_board()
                self.draw_coordinates()
                self.draw_pieces()
                self.draw_highlights()
                return
        self.knights = [
            {"pos": [7, 1], "color": "white", "selected": False},
            {"pos": [7, 6], "color": "white", "selected": False},
            {"pos": [0, 1], "color": "black", "selected": False},
            {"pos": [0, 6], "color": "black", "selected": False},
        ]
        self.white_king_pos = [7, 4]
        self.black_king_pos = [0, 4]
        self.white_king_selected = False
        self.black_king_selected = False
        self.legal_moves = []
        self.second_moves_groups = []
        self.right_click_pos = None
        self.right_click_second_pos = None
        self.right_click_third_pos = None
        self.right_click_fourth_pos = None
        self.right_click_second_moves = []
        self.right_click_third_moves = []
        self.right_click_fourth_moves = []
        self.show_move_numbers = False
        self.other_pieces = []
        self.add_piece_mode = False
        self.add_piece_selected = None
        self.add_piece_square = None
        self.board = chess.Board()
        self.last_random_game_set = False
        self.last_random_game_state = None
        self.history = []
        self.redo_stack = []
        self.game = None
        self.move_list = []
        self.current_move = 0
        self.to_start_btn['state'] = tk.DISABLED
        self.back_btn['state'] = tk.DISABLED
        self.forward_btn['state'] = tk.DISABLED
        self.to_end_btn['state'] = tk.DISABLED
        self.game_name_var.set("")
        self.to_move_var.set("")
        self.draw_board()
        self.draw_coordinates()
        self.draw_pieces()
        self.draw_highlights()
    def add_random_game(self):
        self.save_state()
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            try:
                headers = {
                    'User-Agent': 'username: chessknightapp, email: chessknightapp@protonmail.com'
                }
                players = ["Hikaru", "MagnusCarlsen", "FabianoCaruana", "LevonAronian", "DingLiren", "BodhanaS"]
                username = random.choice(players)
                archive_url = f"https://api.chess.com/pub/player/{username}/games/archives"
                response = requests.get(archive_url, headers=headers)
                if response.status_code == 403:
                    raise Exception("403 Forbidden: Check User-Agent header or IP restrictions. Use a valid username/email.")
                if response.status_code == 429:
                    raise Exception("429 Rate Limit Exceeded: Wait and try again later.")
                response.raise_for_status()
                archives = response.json().get("archives", [])
                if not archives:
                    raise ValueError("No archives found for player")
                recent_archives = archives[-6:] if len(archives) > 6 else archives
                archive_url = random.choice(recent_archives)
                response = requests.get(archive_url, headers=headers)
                if response.status_code == 403:
                    raise Exception("403 Forbidden: Check User-Agent header or IP restrictions.")
                if response.status_code == 429:
                    raise Exception("429 Rate Limit Exceeded: Wait and try again later.")
                response.raise_for_status()
                games = response.json().get("games", [])
                if not games:
                    raise ValueError("No games found in archive")
                game = random.choice(games)
                pgn = game.get("pgn")
                if not pgn:
                    raise ValueError("No PGN found for game")
                game_pgn = chess.pgn.read_game(io.StringIO(pgn))
                if not game_pgn:
                    raise ValueError("Invalid PGN")
                board = game_pgn.board()
                move_count = len(list(game_pgn.mainline_moves())) // 2
                if move_count < 10:
                    raise ValueError("Game too short")
                phase = random.choice(["middle", "end"])
                if phase == "middle":
                    target_move = random.randint(10, min(30, move_count))
                else:
                    target_move = move_count
                    temp_board = board.copy()
                    for i, move in enumerate(game_pgn.mainline_moves()):
                        temp_board.push(move)
                        piece_count = sum(1 for sq in chess.SQUARES for p in [temp_board.piece_at(sq)] if p and p.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN])
                        if piece_count <= 6 and i // 2 >= 10:
                            target_move = (i + 1) // 2
                            break
                board = game_pgn.board()
                i = 0
                for move in game_pgn.mainline_moves():
                    if i // 2 >= target_move:
                        break
                    if move in board.legal_moves:
                        board.push(move)
                    else:
                        raise chess.IllegalMoveError(f"Illegal move {move} in position {board.fen()}")
                    i += 1
                self.board = board
                self.knights = []
                self.white_king_pos = None
                self.black_king_pos = None
                self.other_pieces = []
                for square in chess.SQUARES:
                    piece = board.piece_at(square)
                    if piece:
                        row, col = 7 - (square // 8), square % 8
                        pos = [row, col]
                        if piece.piece_type == chess.KNIGHT:
                            color = "white" if piece.color == chess.WHITE else "black"
                            self.knights.append({"pos": pos, "color": color, "selected": False})
                        elif piece.piece_type == chess.KING:
                            if piece.color == chess.WHITE:
                                self.white_king_pos = pos
                            else:
                                self.black_king_pos = pos
                        else:
                            self.other_pieces.append({"pos": pos, "type": piece.symbol()})
                if not self.knights:
                    self.knights = [
                        {"pos": [7, 1], "color": "white", "selected": False},
                        {"pos": [0, 1], "color": "black", "selected": False}
                    ]
                self.white_king_selected = False
                self.black_king_selected = False
                self.legal_moves = []
                self.second_moves_groups = []
                self.right_click_pos = None
                self.right_click_second_pos = None
                self.right_click_third_pos = None
                self.right_click_fourth_pos = None
                self.right_click_second_moves = []
                self.right_click_third_moves = []
                self.right_click_fourth_moves = []
                self.show_move_numbers = False
                self.last_random_game_state = {
                    "knights": [knight.copy() for knight in self.knights],
                    "white_king_pos": self.white_king_pos[:] if self.white_king_pos else None,
                    "black_king_pos": self.black_king_pos[:] if self.black_king_pos else None,
                    "other_pieces": [piece.copy() for piece in self.other_pieces],
                    "board_fen": self.board.fen() if self.board else None
                }
                self.last_random_game_set = True
                self.game = game_pgn
                self.move_list = list(game_pgn.mainline_moves())
                self.current_move = i
                self.to_start_btn['state'] = tk.NORMAL
                self.back_btn['state'] = tk.NORMAL
                self.forward_btn['state'] = tk.NORMAL
                self.to_end_btn['state'] = tk.NORMAL
                os.makedirs('pgn', exist_ok=True)
                filename = self.game_name_var.get().replace(" ", "_").replace("/", "_") + ".pgn"
                file_path = os.path.join('pgn', filename)
                with open(file_path, 'w') as f:
                    f.write(pgn)
                break
            except (chess.IllegalMoveError, ValueError, requests.RequestException) as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                attempt += 1
                if attempt == max_attempts:
                    tk.messagebox.showerror("Error", f"Failed to load random game after {max_attempts} attempts: {str(e)}")
                    self.reset()
                    return
               
        game_pgn = chess.pgn.read_game(io.StringIO(pgn))
        # Get player names and event/date for display
        white = game_pgn.headers.get("White", "White")
        black = game_pgn.headers.get("Black", "Black")
        date = game_pgn.headers.get("Date", "")
        event = game_pgn.headers.get("Event", "")
        self.game_name_var.set(f"{white} vs {black} {date} {event}")
        # Assuming you already have your PGN string in 'pgn'
        game_pgn = chess.pgn.read_game(io.StringIO(pgn))
        # Create a board and play out all the moves from the game
        board = game_pgn.board()
        for move in game_pgn.mainline_moves():
            board.push(move)
        # Now set the label based on the side to move in the final position
        to_move = "White" if board.turn == chess.WHITE else "Black"
        self.to_move_var.set(f"{to_move} to move")
        # Set the "to move" label
        if game_pgn is not None:
            # After you have set up self.board = board, or just before drawing
            try:
                to_move = "White" if board.turn == chess.WHITE else "Black"
                self.to_move_var.set(f"{to_move} to move")
            except Exception:
                self.to_move_var.set("")
        else:
            self.to_move_var.set("")
        self.draw_board()
        self.draw_coordinates()
        self.draw_pieces()
        self.draw_highlights()
    def new_standard_game(self):
        self.save_state()
        self.knights = []
        self.other_pieces = []
        self.white_king_pos = None
        self.black_king_pos = None
        board = chess.Board()
        self.board = board
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                row, col = 7 - (square // 8), square % 8
                pos = [row, col]
                if piece.piece_type == chess.KNIGHT:
                    color = "white" if piece.color == chess.WHITE else "black"
                    self.knights.append({"pos": pos, "color": color, "selected": False})
                elif piece.piece_type == chess.KING:
                    if piece.color == chess.WHITE:
                        self.white_king_pos = pos
                    else:
                        self.black_king_pos = pos
                else:
                    self.other_pieces.append({"pos": pos, "type": piece.symbol()})
        self.white_king_selected = False
        self.black_king_selected = False
        self.legal_moves = []
        self.second_moves_groups = []
        self.right_click_pos = None
        self.right_click_second_pos = None
        self.right_click_third_pos = None
        self.right_click_fourth_pos = None
        self.right_click_second_moves = []
        self.right_click_third_moves = []
        self.right_click_fourth_moves = []
        self.show_move_numbers = False
        self.add_piece_mode = False
        self.add_piece_selected = None
        self.add_piece_square = None
        self.last_random_game_set = False
        self.last_random_game_state = None
        self.game = None
        self.move_list = []
        self.current_move = 0
        self.to_start_btn['state'] = tk.DISABLED
        self.back_btn['state'] = tk.DISABLED
        self.forward_btn['state'] = tk.DISABLED
        self.to_end_btn['state'] = tk.DISABLED
        self.game_name_var.set("")
        self.to_move_var.set("")
        self.draw_board()
        self.draw_coordinates()
        self.draw_pieces()
        self.draw_highlights()
    def open_color_settings_window(self):
        win = tk.Toplevel(self.root)
        win.title("Adjust Knight Highlight Colors")
        win.geometry("400x400")
        row = 0
        # 1st move color
        tk.Label(win, text="1st Move Highlight (Gold):").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        first_btn = tk.Button(win, bg=self.first_move_color, width=6, command=lambda: self.choose_and_set_color('first'))
        first_btn.grid(row=row, column=1, padx=8)
        row += 1
        # Create buttons for each 2nd move color
        self.color_btns = []
        for idx, color in enumerate(self.second_move_colors):
            tk.Label(win, text=f"2nd Move Group {idx+1}:").grid(row=row, column=0, sticky="w", padx=8, pady=5)
            btn = tk.Button(win, bg=color, width=6,
                            command=lambda i=idx: self.choose_and_set_color(i))
            btn.grid(row=row, column=1, padx=8)
            self.color_btns.append(btn)
            row += 1
        # Right-click colors
        tk.Label(win, text="Right-click 2nd Move:").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        rc_btn = tk.Button(win, bg=self.right_click_color, width=6, command=lambda: self.choose_and_set_color('rc'))
        rc_btn.grid(row=row, column=1, padx=8)
        row += 1
        tk.Label(win, text="Right-click 3rd Move:").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        third_btn = tk.Button(win, bg=self.third_move_color, width=6, command=lambda: self.choose_and_set_color('third'))
        third_btn.grid(row=row, column=1, padx=8)
        row += 1
        tk.Label(win, text="Right-click 4th Move:").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        fourth_btn = tk.Button(win, bg=self.fourth_move_color, width=6, command=lambda: self.choose_and_set_color('fourth'))
        fourth_btn.grid(row=row, column=1, padx=8)
        row += 1
        # Save reference to buttons for updating color
        self._color_settings_widgets = {
            "first": first_btn,
            "second": self.color_btns,
            "rc": rc_btn,
            "third": third_btn,
            "fourth": fourth_btn,
        }
    def choose_and_set_color(self, which):
        # Open a color chooser dialog
        color_code = colorchooser.askcolor(title="Choose highlight color")
        if color_code and color_code[1]:
            color = color_code[1]
            if which == "first":
                self.first_move_color = color
                self._color_settings_widgets["first"].configure(bg=color)
            elif which == "rc":
                self.right_click_color = color
                self._color_settings_widgets["rc"].configure(bg=color)
            elif which == "third":
                self.third_move_color = color
                self._color_settings_widgets["third"].configure(bg=color)
            elif which == "fourth":
                self.fourth_move_color = color
                self._color_settings_widgets["fourth"].configure(bg=color)
            elif isinstance(which, int):
                self.second_move_colors[which] = color
                self._color_settings_widgets["second"][which].configure(bg=color)
            self.save_colors()
            self.draw_board()
            self.draw_coordinates()
            self.draw_pieces()
            self.draw_highlights()
    def save_colors(self):
        data = {
            'first_move_color': self.first_move_color,
            'second_move_colors': self.second_move_colors,
            'right_click_color': self.right_click_color,
            'third_move_color': self.third_move_color,
            'fourth_move_color': self.fourth_move_color,
            'use_green_theme': self.use_green_theme,
        }
        with open('colors.cfg', 'w') as f:
            json.dump(data, f)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessKnightApp(root)
    root.mainloop()