from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

class MinimalButtonApp(App):
    """Demo app showing minimal-sized buttons."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    Vertical {
        width: auto;
        height: auto;
    }
    
    .minimal-button {
        min-width: 0;
        width: auto;
        height: 1;
        padding: 0 1;
        margin: 0;
    }
    
    .section-title {
        margin: 2 0 1 0;
        text-style: bold;
    }
    
    Horizontal {
        width: auto;
        height: auto;
        margin: 1 0;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Minimal Buttons Demo", classes="section-title")
            
            with Horizontal():
                yield Button("OK", classes="minimal-button")
                yield Button("Cancel", classes="minimal-button")
                yield Button("Save", classes="minimal-button")
            
            yield Static("Standard Buttons (for comparison)", classes="section-title")
            
            with Horizontal():
                yield Button("OK")
                yield Button("Cancel")
                yield Button("Save")
            
            yield Static("Various Minimal Sizes", classes="section-title")
            
            with Horizontal():
                yield Button("X", classes="minimal-button")
                yield Button("Go", classes="minimal-button")
                yield Button("Submit", classes="minimal-button")
                yield Button("Download File", classes="minimal-button")

if __name__ == "__main__":
    app = MinimalButtonApp()
    app.run()