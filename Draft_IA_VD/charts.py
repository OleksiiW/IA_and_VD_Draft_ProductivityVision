import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from matplotlib.colors import LogNorm
from config import Config


class ChartBuilder:
    """Клас для генерації графіків Matplotlib/Seaborn для GUI"""

    @staticmethod
    def _darken(rgb, factor=0.7):
        return rgb[0] * factor, rgb[1] * factor, rgb[2] * factor

    @staticmethod
    def create_3d_donut(df: pd.DataFrame, column: str, title: str) -> Figure:
        counts = df[column].dropna().astype(str).value_counts()
        labels = counts.index.tolist()
        sizes = counts.values
        total = sizes.sum()

        colors_top = sns.color_palette("pastel", n_colors=len(labels))
        colors_side = [ChartBuilder._darken(c, factor=0.7) for c in colors_top]

        fig = Figure(figsize=(8, 6), dpi=100)
        fig.patch.set_facecolor(Config.COLOR_BG_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(Config.COLOR_BG_CARD)

        thickness, n_layers, width, start_angle = 0.35, 20, 0.55, 90

        for i in range(n_layers):
            offset = (i / n_layers) * thickness
            ax.pie(sizes, radius=1.1, startangle=start_angle, colors=colors_side,
                   center=(0, -thickness + offset),
                   wedgeprops=dict(width=width, edgecolor="none", antialiased=True))

        wedges, _ = ax.pie(sizes, radius=1.1, startangle=start_angle, colors=colors_top,
                           center=(0, 0),
                           wedgeprops=dict(width=width, edgecolor="white", linewidth=0.6, antialiased=True))

        ax.set_ylim(-1.0, 1.0)
        ax.set_aspect(0.45)
        ax.set_title(title, fontsize=14, fontweight="bold", color="white", pad=20)

        legend_labels = [f"{lab}: {val} ({val / total:.1%})" for lab, val in zip(labels, sizes)]
        ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0.5),
                  frameon=False, fontsize=10, labelcolor="white")
        fig.tight_layout()
        return fig

    @staticmethod
    def create_countplot_horiz(df: pd.DataFrame, col: str, title: str) -> Figure:
        dept = df[col].dropna().astype(str)
        order = dept.value_counts().index

        fig = Figure(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor(Config.COLOR_BG_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(Config.COLOR_BG_CARD)

        sns.countplot(y=dept, order=order, color=Config.BAR_COLOR, edgecolor=None, ax=ax)

        ax.set_title(title, color="white")
        ax.set_xlabel("Amount", color="white")
        ax.set_ylabel("", color="white")
        ax.tick_params(colors='white')
        ax.grid(True, axis="x", alpha=0.12)
        sns.despine(ax=ax)

        total = len(dept)
        for p in ax.patches:
            count = int(p.get_width())
            pct = count / total * 100
            ax.annotate(f"{pct:.1f}%", (p.get_width(), p.get_y() + p.get_height() / 2),
                        ha="left", va="center", fontsize=9, color="white", xytext=(6, 0), textcoords="offset points")
        fig.tight_layout()
        return fig

    @staticmethod
    def create_countplot_vertical(df: pd.DataFrame, col: str, title: str) -> Figure:
        data = pd.to_numeric(df[col], errors="coerce").dropna().astype(int)
        order = list(range(int(data.min()), int(data.max()) + 1))

        fig = Figure(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor(Config.COLOR_BG_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(Config.COLOR_BG_CARD)

        sns.countplot(x=data, order=order, color=Config.BAR_COLOR, edgecolor=None, ax=ax)

        ax.set_title(title, color="white")
        ax.set_xlabel(col, color="white")
        ax.set_ylabel("Count", color="white")
        ax.tick_params(colors='white')
        ax.grid(True, axis="y", alpha=0.12)
        sns.despine(ax=ax)

        total = len(data)
        for p in ax.patches:
            count = int(p.get_height())
            pct = count / total * 100
            ax.annotate(f"{pct:.1f}%", (p.get_x() + p.get_width() / 2, p.get_height()),
                        ha="center", va="bottom", fontsize=9, color="white", xytext=(0, 4), textcoords="offset points")
        fig.tight_layout()
        return fig

    @staticmethod
    def create_hist_kde(df: pd.DataFrame, col: str, bins: int, title: str) -> Figure:
        x = pd.to_numeric(df[col], errors="coerce").dropna()

        fig = Figure(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor(Config.COLOR_BG_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(Config.COLOR_BG_CARD)

        sns.histplot(x, bins=bins, kde=True, color=Config.BAR_COLOR, edgecolor=None, ax=ax)
        ax.set_title(title, color="white")
        ax.set_xlabel(col, color="white")
        ax.set_ylabel("Count", color="white")
        ax.tick_params(colors='white')
        ax.grid(True, axis="y", alpha=0.12)
        sns.despine(ax=ax)
        fig.tight_layout()
        return fig

    @staticmethod
    def create_violin(df: pd.DataFrame, col: str, title: str) -> Figure:
        x = pd.to_numeric(df[col], errors="coerce").dropna()
        long = pd.DataFrame({"Metric": [col] * len(x), "Value": x})

        fig = Figure(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor(Config.COLOR_BG_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(Config.COLOR_BG_CARD)

        sns.violinplot(data=long, x="Metric", y="Value", inner="quartile", cut=0, linewidth=1.1,
                       palette=[Config.VIOLIN_PALETTE[1]], saturation=1, ax=ax)
        ax.set_title(title, color="white")
        ax.set_xlabel("", color="white")
        ax.tick_params(colors='white')
        sns.despine(ax=ax)
        fig.tight_layout()
        return fig

    @staticmethod
    def create_hist2d(df: pd.DataFrame, x_col: str, y_col: str, bins: int, title: str) -> Figure:
        x = pd.to_numeric(df[x_col], errors="coerce")
        y = pd.to_numeric(df[y_col], errors="coerce")
        d = pd.DataFrame({x_col: x, y_col: y}).dropna()

        fig = Figure(figsize=(8, 6), dpi=100)
        fig.patch.set_facecolor(Config.COLOR_BG_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(Config.COLOR_BG_CARD)

        h = ax.hist2d(d[x_col], d[y_col], bins=bins, cmap=Config.KDE_CMAP, norm=LogNorm())
        ax.set_title(title, color="white")
        ax.set_xlabel(x_col, color="white")
        ax.set_ylabel(y_col, color="white")
        ax.tick_params(colors='white')
        fig.tight_layout()
        return fig
