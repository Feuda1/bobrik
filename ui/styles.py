from config import COLORS, FONTS

MAIN_WINDOW_STYLE = f"""
    QMainWindow {{
        background-color: {COLORS['background']};
    }}
    QWidget {{
        background-color: {COLORS['background']};
        color: {COLORS['text']};
    }}
"""

HEADER_STYLE = f"""
    QFrame {{
        background-color: {COLORS['panel']};
        border-bottom: 2px solid {COLORS['border']};
    }}
"""

LOGO_STYLE = f"""
    QLabel {{
        color: {COLORS['white']};
        font-size: {FONTS['logo']['size']}px;
        font-weight: {FONTS['logo']['weight']};
    }}
"""

PANEL_STYLE = f"""
    QFrame {{
        background-color: {COLORS['panel']};
        border-radius: 8px;
        border: 1px solid {COLORS['border']};
    }}
"""

TITLE_STYLE = f"""
    QLabel {{
        color: {COLORS['white']};
        font-size: {FONTS['title']['size']}px;
        font-weight: {FONTS['title']['weight']};
        padding-bottom: 5px;
    }}
"""

CONSOLE_STYLE = f"""
    QTextEdit {{
        background-color: #000000;
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        padding: 10px;
        color: {COLORS['text_secondary']};
        font-family: {FONTS['console']['family']};
        font-size: {FONTS['console']['size']}px;
        line-height: 1.4;
    }}
    QTextEdit::selection {{
        background-color: #264f78;
    }}
"""

def get_button_style(is_disabled):
    if is_disabled:
        return f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {COLORS['success_bg']},
                    stop: 1 #043927);
                border: 2px solid {COLORS['success_border']};
                border-radius: 6px;
                color: {COLORS['success']};
                font-size: {FONTS['button']['size']}px;
                font-weight: {FONTS['button']['weight']};
                padding: 15px;
                text-align: center;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #087f5b,
                    stop: 1 #065f46);
                border-color: #34d399;
            }}
            QPushButton:pressed {{
                background: #065f46;
                border-color: {COLORS['success']};
            }}
        """
    else:
        return f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {COLORS['button']},
                    stop: 1 #171717);
                border: 2px solid #2d2d2d;
                border-radius: 6px;
                color: {COLORS['text']};
                font-size: {FONTS['button']['size']}px;
                font-weight: {FONTS['button']['weight']};
                padding: 15px;
                text-align: center;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {COLORS['button_hover']},
                    stop: 1 #1f1f1f);
                border-color: #3d3d3d;
            }}
            QPushButton:pressed {{
                background: {COLORS['button_active']};
                border-color: #2d2d2d;
            }}
        """