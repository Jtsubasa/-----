import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
import numpy as np

class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Graph")

        # 初期グラフ
        self.G = nx.Graph()
        self.G.add_node(1, pos=(0, 0), color='white')  # 初期ノード
        self.selected_node = None
        self.mode = "add_node"  # "add_node" または "insert_node_between"

        # 操作履歴管理
        self.history = []
        self.redo_stack = []

        # Tkinterレイアウトの設定
        self.canvas = tk.Canvas(root)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # グラフ描画用のmatplotlib Figure
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=self.canvas)
        self.canvas_plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 操作ボタンの作成
        self.undo_button = tk.Button(root, text="元に戻す", command=self.undo)
        self.undo_button.pack(side=tk.LEFT)

        self.redo_button = tk.Button(root, text="やり直す", command=self.redo)
        self.redo_button.pack(side=tk.LEFT)

        self.delete_button = tk.Button(root, text="削除", command=self.reset_graph)
        self.delete_button.pack(side=tk.LEFT)

        self.add_node_mode_button = tk.Button(root, text="ノード追加モード", command=self.set_add_node_mode)
        self.add_node_mode_button.pack(side=tk.LEFT)

        self.insert_node_mode_button = tk.Button(root, text="間に挿入モード", command=self.set_insert_node_mode)
        self.insert_node_mode_button.pack(side=tk.LEFT)

        # クリックイベントのバインディング
        self.canvas_plot.mpl_connect("button_press_event", self.on_click)

        self.draw_graph()

    def setup_menu(self):
        """ メニューバーの設定 """
        menubar = tk.Menu(self.root)

        # 操作メニュー
        operation_menu = tk.Menu(menubar, tearoff=0)
        operation_menu.add_command(label="ノードを追加", command=self.add_node_with_branch, accelerator="Ctrl+N")
        operation_menu.add_command(label="間にノードを追加", command=self.add_node_between, accelerator="Ctrl+B")
        menubar.add_cascade(label="操作", menu=operation_menu)

        # 編集メニュー
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="削除", command=self.reset_graph, accelerator="Ctrl+D")
        menubar.add_cascade(label="編集", menu=edit_menu)

        # メニューバーを表示
        self.root.config(menu=menubar)

        # ショートカットキーの設定
        self.root.bind("<Control-n>", lambda event: self.add_node_with_branch())
        self.root.bind("<Control-b>", lambda event: self.add_node_between())
        self.root.bind("<Control-d>", lambda event: self.reset_graph())

    
    def set_add_node_mode(self):
        """ ノード追加モードに切り替え """
        self.mode = "add_node"
        self.selected_node = None

    def set_insert_node_mode(self):
        """ ノード間挿入モードに切り替え """
        self.mode = "insert_node_between"
        self.selected_node = None

    def draw_graph(self):
        """ グラフを描画 """
        pos = nx.get_node_attributes(self.G, 'pos')
        colors = [self.G.nodes[node]['color'] for node in self.G.nodes]

        # ノードの描画
        nx.draw(self.G, pos, with_labels=False, node_color=colors, node_size=500, font_size=16)

        # ラベルをノードに応じて色分けして表示
        labels = {node: node for node in self.G.nodes}
        label_colors = {node: 'white' if self.G.nodes[node]['color'] == 'black' else 'black' for node in self.G.nodes}
        nx.draw_networkx_labels(self.G, pos, labels=labels, font_color=label_colors)

        # 描画の更新
        self.canvas.draw()


    def add_node_with_branch(self, selected_node):
        pos = nx.get_node_attributes(self.G, 'pos')
        x, y = pos[selected_node]

        # 新しいノードの位置を計算
        angle = np.random.uniform(0, 2 * np.pi)
        r = 1
        new_x = x + r * np.cos(angle)
        new_y = y + r * np.sin(angle)

        new_node = len(self.G.nodes) + 1
        self.G.add_node(new_node, pos=(new_x, new_y), color='white')
        self.G.add_edge(selected_node, new_node)

        # 選択されたノードの色を反転
        self.flip_color(selected_node)

        # 新しいノードに隣接するノードの色を反転（ただし、selected_node は除外）
        self.flip_adjacent_node_colors(new_node, exclude_node=selected_node)

        # グラフを再描画
        self.draw_graph()


    def insert_node_between(self, node1, node2):
        """ エッジ間にノードを挿入 """
        if self.G.has_edge(node1, node2):
            pos1 = self.G.nodes[node1]['pos']
            pos2 = self.G.nodes[node2]['pos']
            mid_pos = [(p1 + p2) / 2 for p1, p2 in zip(pos1, pos2)]

            # 既存のエッジを削除して新しいノードを追加
            self.G.remove_edge(node1, node2)
            new_node = len(self.G.nodes) + 1
            self.G.add_node(new_node, pos=mid_pos, color='white')
            self.G.add_edge(node1, new_node)
            self.G.add_edge(new_node, node2)

            # 両端のノードの色を反転
            self.flip_color(node1)
            self.flip_color(node2)

    def flip_color(self, node):
        """ ノードの色を反転 """
        current_color = self.G.nodes[node]['color']
        print(f"Node {node} current color: {current_color}")  # デバッグ用
        new_color = 'black' if current_color == 'white' else 'white'
        self.G.nodes[node]['color'] = new_color
        print(f"Node {node} new color: {new_color}")  # デバッグ用

    def flip_adjacent_node_colors(self, node, exclude_node=None):
        """ 隣接するノードの色を反転、ただし exclude_node は除外 """
        for neighbor in self.G.neighbors(node):
            if neighbor != exclude_node:  # exclude_node（selected_node）があれば反転をスキップ
                self.flip_color(neighbor)

    def on_click(self, event):
        """ マウスクリックイベント処理 """
        if event.xdata is None or event.ydata is None:
            return  # クリックが無効な領域だった場合

        if self.mode == "add_node":
            if self.selected_node is None:  # ノードを選択
                self.selected_node = self.find_nearest_node(event.xdata, event.ydata)
            else:  # 選択されたノードから新しいノードを追加
                self.add_node_with_branch(self.selected_node)
                self.selected_node = None

        elif self.mode == "insert_node_between":
            if self.selected_node is None:  # 最初のノードを選択
                self.selected_node = self.find_nearest_node(event.xdata, event.ydata)
            else:  # 2つ目のノードを選択して、その間にノードを挿入
                second_node = self.find_nearest_node(event.xdata, event.ydata)
                if not self.G.has_edge(self.selected_node, second_node):
                    messagebox.showerror("エラー", "選択したノードの間にエッジが存在しません")
                else:
                    self.insert_node_between(self.selected_node, second_node)
                self.selected_node = None

        self.history.append(self.G.copy())
        self.redo_stack.clear()

        self.draw_graph()

    def find_nearest_node(self, x, y):
        """ 最も近いノードを見つける """
        pos = nx.get_node_attributes(self.G, 'pos')
        nearest_node = min(self.G.nodes, key=lambda n: np.linalg.norm(np.array(pos[n]) - np.array([x, y])))
        return nearest_node

    def reset_graph(self):
        """ すべてのノードを削除し、白いノードを一つ配置して初期化 """
        # グラフの全ノードとエッジを削除
        self.G.clear()

        # 白いノードを一つ配置
        self.G.add_node(1, pos=(0, 0), color='white')

        # グラフを再描画
        self.draw_graph()

    def undo(self):
        """ 元に戻す """
        if self.history:
            self.redo_stack.append(self.G.copy())
            self.G = self.history.pop()
            self.draw_graph()

    def redo(self):
        """ やり直す """
        if self.redo_stack:
            self.history.append(self.G.copy())
            self.G = self.redo_stack.pop()
            self.draw_graph()

# Tkinterアプリケーションの実行
root = tk.Tk()
app = GraphApp(root)
root.mainloop()
