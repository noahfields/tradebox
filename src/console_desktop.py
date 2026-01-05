from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Grid
from textual.screen import ModalScreen
from textual.widgets import (
	Button,
	DataTable,
	Footer,
	Header,
	Label,
	Static,
	TabbedContent,
	TabPane,
)

import database


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
		with Container(id="container-runner-status"):
			yield RunnerStatus(id="runner-status")

		with Container(id="container_positions_datatable"):
			yield DataTablePositions(id="datatable_positions")

		with Horizontal(id="positions_buttons"):
			yield Button("Sell Market", variant="primary", id="button-position-sell-market", classes="small-button")
			yield Button("Sell Limit", variant="primary", id="button-position-sell-limit", classes="small-button")
			yield Button("Buy Market", variant="primary", id="button-position-buy-market", classes="small-button")
			yield Button("Buy Limit", variant="primary", id="button-position-buy-limit", classes="small-button")
			yield Button("Sell Trailing", variant="primary", id="button-position-sell-trailing", classes="small-button")
			yield Button("Sell Bracket", variant="primary", id="button-position-sell-bracket", classes="small-button")
			yield Button("Sell All @ Market", variant="error", id="button-position-sell-all-market", classes="small-button")

class TabPaneSystemManagement(TabPane):
	def compose(self) -> ComposeResult:
		yield Static("sys mgmt tab pane")

class RunnerStatus(Static):
	def compose(self) -> ComposeResult:
		with Horizontal():
			with Horizontal(classes="runner-status-section"):
				yield Label("Positions")
				yield Label(" ", id="runner-update-open-option-positions-active", classes="active-label")
				yield Label(" ", id="runner-update-open-option-positions-status", classes="status-label")

			with Horizontal(classes="runner-status-section"):
				yield Label("Position Market Data")
				yield Label(" ", id="runner-update-open-option-positions-market-data-active", classes="active-label")
				yield Label(" ", id="runner-update-open-option-positions-market-data-status", classes="status-label")

			with Horizontal(classes="runner-status-section"):
				yield Label("Broker Orders")
				yield Label(" ", id="runner-update-open-broker-option-orders-active", classes="active-label")
				yield Label(" ", id="runner-update-open-broker-option-orders-status", classes="status-label")

			with Horizontal(classes="runner-status-section"):
				yield Label("Broker Orders Market Data")
				yield Label(" ", id="runner-broker-orders-market-data-active", classes="active-label")
				yield Label(" ", id="runner-broker-orders-market-data-status", classes="status-label")

			with Horizontal(classes="runner-status-section"):
				yield Label("Trigger Market Data")
				yield Label(" ", id="runner-trigger-market-data-active", classes="active-label")
				yield Label(" ", id="runner-trigger-market-data-status", classes="status-label")

			with Horizontal(classes="runner-status-section"):
				yield Label("Trailing Orders")
				yield Label(" ", id="runner-trailing-orders-active", classes="active-label")
				yield Label(" ", id="runner-trailing-orders-status", classes="status-label")

			with Horizontal(classes="runner-status-section"):
				yield Label("Trailing Market Data")
				yield Label(" ", id="runner-trailing-orders-market-data-active", classes="active-label")
				yield Label(" ", id="runner-trailing-orders-market-data-status", classes="status-label")

			with Horizontal(classes="runner-status-section"):
				yield Label("Bracket Orders")
				yield Label(" ", id="runner-bracket-orders-active", classes="active-label")
				yield Label(" ", id="runner-bracket-orders-status", classes="status-label")

			with Horizontal(classes="runner-status-section"):
				yield Label("Bracket Market Data")
				yield Label(" ", id="runner-bracket-orders-market-data-active", classes="active-label")
				yield Label(" ", id="runner-bracket-orders-market-data-status", classes="status-label")

	def on_mount(self) -> None:
		self.set_interval(1, self.refresh_data)

	def refresh_data(self) -> None:
		runners_status_list = database.get_all_runners_status()
		for runner_status in runners_status_list:
			active_label = self.query_one(
				f"#runner-{runner_status['runner_name'].replace('_', '-')}-active", Label
			)
			status_label = self.query_one(
				f"#runner-{runner_status['runner_name'].replace('_', '-')}-status", Label
			)

			if runner_status["active"]:
				active_label.styles.background = "green"
			else:
				active_label.styles.background = "red"

			if runner_status["last_update_successful"]:
				status_label.styles.background = "green"
			else:
				status_label.styles.background = "red"


class DataTablePositions(DataTable):
	def on_mount(self) -> None:
		"""Set up the data table and start auto-refresh."""
		# table = self.query_one("#positions-table", DataTable)
		self.cursor_type = "row"
		self.zebra_stripes = True

		# Add columns
		self.add_column("ID", key="id", width=6)
		self.add_column("Symbol", key="symbol", width=8)
		self.add_column("Type", key="type", width=6)
		self.add_column("Strike", key="strike", width=10)
		self.add_column("Expiry", key="expiry", width=12)
		self.add_column("Qty", key="qty", width=6)
		self.add_column("Avg Price", key="avg_price", width=12)
		self.add_column("Current", key="current", width=12)
		self.add_column("P/L", key="pl", width=12)
		self.add_column("P/L %", key="pl_pct", width=10)

		# Load initial data
		# self.refresh_data()

		# Start auto-refresh
		# self.set_interval(self.refresh_interval, self.refresh_data)

	def refresh_data(self) -> None:
		pass




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
	app.theme = "nord"
	app.run()
