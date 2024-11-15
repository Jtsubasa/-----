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

        # アイコンボタンの作成
        self.undo_button = tk.Button(root, text="元に戻す", command=self.undo)
        self.undo_button.pack(side=tk.LEFT)

        self.redo_button = tk.Button(root, text="やり直す", command=self.redo)
        self.redo_button.pack(side=tk.LEFT)

        self.delete_button = tk.Button(root, text="削除", command=self.delete_all)
        self.delete_button.pack(side=tk.LEFT)

        # クリックイベントのバインディング
        self.canvas_plot.mpl_connect("button_press_event", self.on_click)

        self.draw_graph()

    def draw_graph(self):
        """ グラフを描画する """
        self.ax.clear()
        pos = nx.get_node_attributes(self.G, 'pos')
        node_colors = [self.G.nodes[n]['color'] for n in self.G.nodes()]
        nx.draw(self.G, pos, ax=self.ax, with_labels=True, node_color=node_colors,
                node_size=800, font_color='black', font_weight='bold', edgecolors='black')

        self.canvas_plot.draw()

    def add_node(self, x, y):
        """ ノードを追加する処理 """
        new_node = len(self.G.nodes) + 1
        self.G.add_node(new_node, pos=(x, y), color='white')

    def find_nearest_edge(self, x, y):
        """ クリック位置に最も近いエッジを見つける """
        pos = nx.get_node_attributes(self.G, 'pos')
        min_dist = float('inf')
        nearest_edge = None
        nearest_point = None

        for edge in self.G.edges:
            p1 = np.array(pos[edge[0]])
            p2 = np.array(pos[edge[1]])
            v = p2 - p1
            w = np.array([x, y]) - p1
            t = np.dot(w, v) / np.dot(v, v)
            t = max(0, min(1, t))
            projection = p1 + t * v
            dist = np.linalg.norm(projection - np.array([x, y]))

            if dist < min_dist:
                min_dist = dist
                nearest_edge = edge
                nearest_point = projection

        return nearest_edge, nearest_point, min_dist

    def on_click(self, event):
        """ マウスクリックイベント処理 """
        if event.xdata is None or event.ydata is None:
            return  # クリックが無効な領域だった場合
        x, y = event.xdata, event.ydata

        nearest_edge, nearest_point, dist = self.find_nearest_edge(x, y)

        if dist < 0.1:  # クリックがエッジに近ければ、エッジの間にノードを挿入
            self.insert_node_between(nearest_edge, nearest_point)
        else:  # クリックがエッジに近くない場合は、新規ノードを最も近いノードに接続
            self.connect_to_nearest_node(x, y)

        self.history.append(self.G.copy())
        self.redo_stack.clear()

        self.draw_graph()

    def insert_node_between(self, edge, pos):
        """ エッジ間にノードを挿入し、両側の色を反転 """
        new_node = len(self.G.nodes) + 1
        self.G.add_node(new_node, pos=(pos[0], pos[1]), color='white')
        self.G.remove_edge(*edge)
        self.G.add_edge(edge[0], new_node)
        self.G.add_edge(new_node, edge[1])

        # 両端のノードの色を反転
        for node in edge:
            current_color = self.G.nodes[node]['color']
            new_color = 'black' if current_color == 'white' else 'white'
            self.G.nodes[node]['color'] = new_color

    def connect_to_nearest_node(self, x, y):
        """ 最も近いノードと接続し、色を反転 """
        pos = nx.get_node_attributes(self.G, 'pos')
        nearest_node = min(self.G.nodes, key=lambda n: np.linalg.norm(np.array(pos[n]) - np.array([x, y])))
        self.add_node(x, y)
        new_node = len(self.G.nodes)
        self.G.add_edge(nearest_node, new_node)

        # 接続したノードの色を反転
        current_color = self.G.nodes[nearest_node]['color']
        new_color = 'black' if current_color == 'white' else 'white'
        self.G.nodes[nearest_node]['color'] = new_color

    def delete_all(self):
        """ すべてのノードとエッジを削除 """
        self.history.append(self.G.copy())
        self.redo_stack.clear()
        self.G.clear()
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
