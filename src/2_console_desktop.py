from textual.app import App, ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
	Button,
	Footer,
	Header,
	Label,
	Static,
	TabbedContent,
	TabPane,
)


class Tradebox(App):
	CSS_PATH = "tcss/2_console_desktop.tcss"
	BINDINGS = [("q", "request_quit", "Quit")]

	def compose(self) -> ComposeResult:
		yield Header()
		with TabbedContent():
			yield TabPaneMain(title="Main", id="tabpane_main")
			yield TabPaneSystemManagement(
				title="System Management", id="tabpane_system_management"
			)
		yield Footer()

	def action_request_quit(self) -> None:
		self.push_screen(ModalScreenQuit())


class TabPaneMain(TabPane):
	def compose(self) -> ComposeResult:
		with VerticalScroll():
			yield Static("main tab")


class TabPaneSystemManagement(TabPane):
	def compose(self) -> ComposeResult:
		with VerticalScroll():
			yield Static("sys mgmt tab pane")


class ModalScreenQuit(ModalScreen):
    def compose(self) -> ComposeResult:
        with Grid():
            yield Label("Are you sure you want to quit?")
            yield Button("Quit", variant="error", id="quit")
            yield Button("Cancel", variant="primary", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            exit()
        else:
            self.app.pop_screen()


if __name__ == "__main__":
	app = Tradebox()
	app.run()
