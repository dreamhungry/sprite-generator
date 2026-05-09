"""Main entry point for the sprite generator application."""

import gradio as gr

from src.ui.interface import create_ui


def main():
    app = create_ui()
    app.launch(share=False, theme=gr.themes.Soft())


if __name__ == "__main__":
    main()
