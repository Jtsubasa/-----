class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Graph")

        self.G = nx.Graph()
        self.G.add_node(1, pos=(0, 0), color='white')  # 初期ノード

        self.history = []
        self.redo_stack = []

        # モード管理（ノード追加モード or ノード間に追加モード）
        self.mode = "add_node"  # デフォルトはノード追加モード
        self.selected_nodes = []  # 選択されたノードを管理

        # Tkinterレイアウトの設定
        self.canvas = tk.Canvas(root)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=self.canvas)
        self.canvas_plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # モード切替ボタン
        self.add_node_mode_button = tk.Button(root, text="ノード追加モード", command=self.set_add_node_mode)
        self.add_node_mode_button.pack(side=tk.LEFT)

        self.add_between_mode_button = tk.Button(root, text="間にノードを追加", command=self.set_add_between_mode)
        self.add_between_mode_button.pack(side=tk.LEFT)

        self.undo_button = tk.Button(root, text="元に戻す", command=self.undo)
        self.undo_button.pack(side=tk.LEFT)

        self.redo_button = tk.Button(root, text="やり直す", command=self.redo)
        self.redo_button.pack(side=tk.LEFT)

        self.delete_button = tk.Button(root, text="削除", command=self.delete_all)
        self.delete_button.pack(side=tk.LEFT)

        self.canvas_plot.mpl_connect("button_press_event", self.on_click)

        self.draw_graph()

    def set_add_node_mode(self):
        """ ノードを追加するモードに変更 """
        self.mode = "add_node"
        self.selected_nodes.clear()

    def set_add_between_mode(self):
        """ ノードを間に追加するモードに変更 """
        self.mode = "add_between"
        self.selected_nodes.clear()

    def on_click(self, event):
        if event.xdata is None or event.ydata is None:
            return
        x, y = event.xdata, event.ydata
        pos = nx.get_node_attributes(self.G, 'pos')

        # クリック位置に最も近いノードを選択
        nearest_node = min(self.G.nodes, key=lambda n: np.linalg.norm(np.array(pos[n]) - np.array([x, y])))

        if self.mode == "add_node":
            self.select_node(nearest_node)
        elif self.mode == "add_between":
            self.select_node_for_between(nearest_node)

    def select_node(self, node):
        """ ノードを選択し、新規ノードを追加 """
        if node in self.selected_nodes:
            messagebox.showwarning("選択エラー", "このノードはすでに選択されています。")
            return

        self.selected_nodes.append(node)
        self.G.nodes[node]['color'] = 'black' if self.G.nodes[node]['color'] == 'white' else 'white'

        if len(self.selected_nodes) == 1:
            # 1つのノードが選択された状態で新しいノードを追加
            self.add_node_at_selected()

        self.draw_graph()

    def select_node_for_between(self, node):
        """ ノード間にノードを追加するために2つのノードを選択 """
        if node in self.selected_nodes:
            messagebox.showwarning("選択エラー", "このノードはすでに選択されています。")
            return

        self.selected_nodes.append(node)
        self.G.nodes[node]['color'] = 'black' if self.G.nodes[node]['color'] == 'white' else 'white'

        if len(self.selected_nodes) == 2:
            # 2つのノードが選択されたので、その間にノードを追加
            self.add_node_between_selected()

        self.draw_graph()

    def add_node_at_selected(self):
        """ 選択されたノードから新しいノードを追加 """
        if len(self.selected_nodes) == 1:
            selected_node = self.selected_nodes[0]
            pos = nx.get_node_attributes(self.G, 'pos')
            x, y = pos[selected_node]
            new_x, new_y = x + 0.1, y + 0.1  # 仮の位置に新ノードを追加

            new_node = len(self.G.nodes) + 1
            self.G.add_node(new_node, pos=(new_x, new_y), color='white')
            self.G.add_edge(selected_node, new_node)

            # 選択されたノードの色を反転
            self.G.nodes[selected_node]['color'] = 'black' if self.G.nodes[selected_node]['color'] == 'white' else 'white'
            self.selected_nodes.clear()

    def add_node_between_selected(self):
        """ 選択された2つのノードの間に新しいノードを追加 """
        node1, node2 = self.selected_nodes
        if self.G.has_edge(node1, node2):
            edge = (node1, node2)
            mid_x = (self.G.nodes[node1]['pos'][0] + self.G.nodes[node2]['pos'][0]) / 2
            mid_y = (self.G.nodes[node1]['pos'][1] + self.G.nodes[node2]['pos'][1]) / 2

            # エッジ間にノードが存在するか確認
            if any(self.G.has_edge(node1, n) and self.G.has_edge(n, node2) for n in self.G.nodes if n not in [node1, node2]):
                messagebox.showwarning("操作エラー", "このエッジの間にはすでにノードがあります。")
                self.selected_nodes.clear()
                return

            new_node = len(self.G.nodes) + 1
            self.G.add_node(new_node, pos=(mid_x, mid_y), color='white')
            self.G.remove_edge(node1, node2)
            self.G.add_edge(node1, new_node)
            self.G.add_edge(new_node, node2)

            # 両端のノードの色を反転
            self.G.nodes[node1]['color'] = 'black' if self.G.nodes[node1]['color'] == 'white' else 'white'
            self.G.nodes[node2]['color'] = 'black' if self.G.nodes[node2]['color'] == 'white' else 'white'
            self.selected_nodes.clear()

    # 既存のメソッドは変更不要
    def draw_graph(self):
        self.ax.clear()
        pos = nx.get_node_attributes(self.G, 'pos')
        node_colors = [self.G.nodes[n]['color'] for n in self.G.nodes()]
        nx.draw(self.G, pos, ax=self.ax, with_labels=True, node_color=node_colors,
                node_size=800, font_color='black', font_weight='bold', edgecolors='black')
        self.canvas_plot.draw()

    def delete_all(self):
        self.history.append(self.G.copy())
        self.redo_stack.clear()
        self.G.clear()
        self.draw_graph()

    def undo(self):
        if self.history:
            self.redo_stack.append(self.G.copy())
            self.G = self.history.pop()
            self.draw_graph()

    def redo(self):
        if self.redo_stack:
            self.history.append(self.G.copy())
            self.G = self.redo_stack.pop()
            self.draw_graph()

# Tkinterアプリケーションの実行
root = tk.Tk()
app = GraphApp(root)
root.mainloop()
