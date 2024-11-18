import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
import numpy as np

class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("インタラクティブグラフ")

        # 初期グラフを作成（ノード1を白で追加）
        self.G = nx.Graph()
        self.G.add_node(1, pos=(0, 0), state=0)  # 初期ノードの状態は0（白）
        self.selected_node = None  # 選択されたノードを追跡
        self.hovered_node = None   # ホバーされたノードを追跡
        self.mode = "add_node"     # 操作モード（"add_node" または "insert_node_between"）

        # 操作履歴管理（Undo/Redo用）
        self.history = []
        self.redo_stack = []

        # Tkinterレイアウトの設定
        self.canvas = tk.Canvas(root)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # グラフ描画用のmatplotlib Figure
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=self.canvas)
        self.canvas_plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.setup_menu()

        # クリックイベントとホバーイベントのバインディング
        self.canvas_plot.mpl_connect("button_press_event", self.on_click)
        self.canvas_plot.mpl_connect("motion_notify_event", self.on_hover)

        self.draw_graph()

    def setup_menu(self):
        """ メニューバーの設定 """
        menubar = tk.Menu(self.root)

        # 操作メニュー
        operation_menu = tk.Menu(menubar, tearoff=0)
        operation_menu.add_command(label="ノードを追加", command=self.set_add_node_mode, accelerator="Ctrl+N")
        operation_menu.add_command(label="間にノードを追加", command=self.set_insert_node_mode, accelerator="Ctrl+B")
        menubar.add_cascade(label="操作", menu=operation_menu)

        # 編集メニュー
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="リセット", command=self.reset_graph, accelerator="Ctrl+D")
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        menubar.add_cascade(label="編集", menu=edit_menu)

        # メニューバーを表示
        self.root.config(menu=menubar)

        # ショートカットキーの設定
        self.root.bind("<Control-n>", lambda event: self.set_add_node_mode())
        self.root.bind("<Control-b>", lambda event: self.set_insert_node_mode())
        self.root.bind("<Control-d>", lambda event: self.reset_graph())
        self.root.bind("<Control-z>", lambda event: self.undo())
        self.root.bind("<Control-y>", lambda event: self.redo())

    def set_add_node_mode(self):
        """ ノード追加モードに切り替え """
        self.mode = "add_node"
        self.selected_node = None
        self.draw_graph()  # ハイライトが残らないように再描画

    def set_insert_node_mode(self):
        """ ノード間挿入モードに切り替え """
        self.mode = "insert_node_between"
        self.selected_node = None
        self.draw_graph()  # ハイライトが残らないように再描画

    def draw_graph(self):
        """ グラフを描画 """
        self.ax.clear()  # 以前のグラフをクリア
        pos = nx.get_node_attributes(self.G, 'pos')

        # ノードの状態に基づいて色を決定
        colors = []
        for node in self.G.nodes:
            if node == self.hovered_node:
                colors.append('red')  # ホバーされているノードは赤
            elif node == self.selected_node:
                colors.append('blue')  # 選択されたノードは青
            else:
                # ノードの状態（0=白、1=黒）に基づいて色を設定
                state = self.G.nodes[node]['state']
                colors.append('white' if state == 0 else 'black')

        # ノードを描画（白いノードには黒い枠をつける）
        nx.draw(self.G, pos, with_labels=False, node_color=colors, node_size=500, font_size=16, 
                edgecolors='black')  # 黒い枠

        # ノードラベルの描画
        labels = {node: node for node in self.G.nodes}
        label_colors = {node: 'white' if self.G.nodes[node]['state'] == 1 else 'black' for node in self.G.nodes}
        nx.draw_networkx_labels(self.G, pos, labels=labels, font_color=label_colors)

        # 描画の更新
        self.canvas_plot.draw()

    def add_node_with_branch(self, selected_node):
        """ 選択されたノードから新しいノードを追加 """
        pos = nx.get_node_attributes(self.G, 'pos')
        x, y = pos[selected_node]

        # 新しいノードの位置をランダムに計算
        angle = np.random.uniform(0, 2 * np.pi)
        r = 1
        new_x = x + r * np.cos(angle)
        new_y = y + r * np.sin(angle)

        # 新しいノードを追加（状態は白）
        new_node = len(self.G.nodes) + 1
        self.G.add_node(new_node, pos=(new_x, new_y), state=0)  # 新しいノードは状態0（白）
        self.G.add_edge(selected_node, new_node)

        # 選択されたノードの色を反転
        self.flip_state(selected_node)

        # グラフを再描画
        self.draw_graph()

    def insert_node_between(self, node1, node2):
        """ 2つのノードの間に新しいノードを挿入 """
        if self.G.has_edge(node1, node2):
            pos1 = self.G.nodes[node1]['pos']
            pos2 = self.G.nodes[node2]['pos']
            mid_pos = [(p1 + p2) / 2 for p1, p2 in zip(pos1, pos2)]

            # エッジを削除し、新しいノードを追加
            self.G.remove_edge(node1, node2)
            new_node = len(self.G.nodes) + 1
            self.G.add_node(new_node, pos=mid_pos, state=0)  # 新しいノードは状態0（白）
            self.G.add_edge(node1, new_node)
            self.G.add_edge(new_node, node2)

            # 両端のノードの色を反転
            self.flip_state(node1)
            self.flip_state(node2)

            self.draw_graph()

    def flip_state(self, node):
        """ ノードの状態を反転（0→1または1→0） """
        current_state = self.G.nodes[node]['state']
        self.G.nodes[node]['state'] = 1 - current_state  # 状態を反転

    def on_hover(self, event):
        """ ホバーイベント処理（ノードのハイライト表示） """
        if event.xdata is None or event.ydata is None or len(self.G.nodes) == 0:
            return  # 無効なホバーやノードがない場合は無視

        nearest_node = self.find_nearest_node(event.xdata, event.ydata)
        if nearest_node != self.hovered_node:  # 別のノードにホバーしている場合
            self.hovered_node = nearest_node

        # グラフを再描画して変更を反映
        self.draw_graph()

    def on_click(self, event):
        """ クリックイベント処理（ノードの追加・挿入） """
        if event.xdata is None or event.ydata is None:
            return  # 無効なクリックは無視

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

        # 操作履歴を更新し、redoスタックをクリア
        self.history.append(self.G.copy())
        self.redo_stack.clear()

        # グラフを再描画
        self.draw_graph()

    def find_nearest_node(self, x, y):
        """ クリック位置に最も近いノードを見つける """
        pos = nx.get_node_attributes(self.G, 'pos')
        nearest_node = min(self.G.nodes, key=lambda n: np.linalg.norm(np.array(pos[n]) - np.array([x, y])))
        return nearest_node

    def reset_graph(self):
        """ グラフを初期状態にリセット """
        self.G.clear()  # すべてのノードとエッジを削除
        self.G.add_node(1, pos=(0, 0), state=0)  # 初期ノードを追加（状態0=白）

        # 操作履歴とredoスタックをクリア
        self.history.clear()
        self.redo_stack.clear()

        # ホバーと選択されたノードをリセット
        self.hovered_node = None
        self.selected_node = None

        # グラフを再描画
        self.draw_graph()

    def undo(self):
        """ 最後の操作を元に戻す """
        if self.history:
            self.redo_stack.append(self.G.copy())
            self.G = self.history.pop()
            self.draw_graph()

    def redo(self):
        """ 最後の元に戻した操作をやり直す """
        if self.redo_stack:
            self.history.append(self.G.copy())
            self.G = self.redo_stack.pop()
            self.draw_graph()

# Tkinterアプリケーションの実行
root = tk.Tk()
app = GraphApp(root)
root.mainloop()
