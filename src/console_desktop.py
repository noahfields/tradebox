import time

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Grid, ScrollableContainer, VerticalScroll
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
from textual import on

import robin_stocks.robinhood as r

import config
import database
import orders
import systemd


class Tradebox(App):
	CSS_PATH = "tcss/console_desktop.tcss"
	BINDINGS = [("q", "request_quit", "Quit")]

	def compose(self) -> ComposeResult:
		yield Header()
		with TabbedContent():
			yield TabPaneMain(title="Main", id="tabpane_main")
			yield TabPaneStatus(title="Status", id="tabpane_status")
			yield TabPaneSystemManagement(
				title="System Management", id="tabpane_system_management"
			)
		yield Footer()

	def action_request_quit(self) -> None:
		exit()
		#self.push_screen(ModalScreenQuit())


class TabPaneMain(TabPane):
	def compose(self) -> ComposeResult:
		with ScrollableContainer(id="container_positions_datatable"):
			yield DataTablePositions(id="datatable_positions")

			with Horizontal(id="positions_buttons"):
				yield Button("Sell Market", variant="primary", id="button-position-sell-market", classes="small-button")
				yield Button("Sell Limit", variant="primary", id="button-position-sell-limit", classes="small-button")
				yield Button("Buy Market", variant="primary", id="button-position-buy-market", classes="small-button")
				yield Button("Buy Limit", variant="primary", id="button-position-buy-limit", classes="small-button")
				yield Button("Sell Trailing", variant="primary", id="button-position-sell-trailing", classes="small-button")
				yield Button("Sell Bracket", variant="primary", id="button-position-sell-bracket", classes="small-button")
				yield Button("Sell All @ Market", variant="error", id="button-position-sell-all-market", classes="small-button")


class TabPaneStatus(TabPane):
	def compose(self) -> ComposeResult:
		with ScrollableContainer(id="container-runner-status"):
			yield RunnerStatus(id="runner-status")

class TabPaneSystemManagement(TabPane):
	def compose(self) -> ComposeResult:
		with VerticalScroll():
			yield Button("Login RH", variant="primary", id="button-login-robinhood", classes="small-button")
			yield Button("Logout RH", variant="primary", id="button-logout-robinhood", classes="small-button")	
			yield Button("Start Runners", variant="primary", id="button-start-runners", classes="small-button")
			yield Button("Stop Runners", variant="primary", id="button-stop-runners", classes="small-button")		
			yield Button("Install Runners", variant="primary", id="button-install-runners", classes="small-button")
			yield Button("Remove Runners", variant="primary", id="button-remove-runners", classes="small-button")
			yield Button("Enable Runners", variant="primary", id="button-enable-runners", classes="small-button")
			yield Button("Disable Runners", variant="primary", id="button-disable-runners", classes="small-button")
			yield Button("Create Database", variant="primary", id="button-create-database", classes="small-button")
			yield Button("Delete Database", variant="primary", id="button-delete-database", classes="small-button")
	

	@on(Button.Pressed, "#button-start-runners")
	def handle_button_start_runners_click(self) -> None:
		self.notify("button-start-runners was clicked!")
		systemd.start_systemd_services()


	@on(Button.Pressed, "#button-stop-runners")
	def handle_button_stop_runners_click(self) -> None:
		self.notify("button-stop-runners was clicked!")
		systemd.stop_systemd_services()


	@on(Button.Pressed, "#button-install-runners")
	def handle_button_install_runners_click(self) -> None:
		self.notify("button-install-runners was clicked!")
		systemd.install_systemd_services(dest_dir="/etc/systemd/system", overwrite=True)


	@on(Button.Pressed, "#button-remove-runners")
	def handle_button_remove_runners_click(self) -> None:
		self.notify("button-remove-runners was clicked!")
		systemd.remove_systemd_services()


	@on(Button.Pressed, "#button-enable-runners")
	def handle_button_enable_runners_click(self) -> None:
		self.notify("button-enable-runners was clicked!")
		systemd.enable_systemd_services()


	@on(Button.Pressed, "#button-disable-runners")
	def handle_button_disable_runners_click(self) -> None:
		self.notify("button-disable-runners was clicked!")
		systemd.disable_systemd_services()


class RunnerStatus(Static):
	def compose(self) -> ComposeResult:
		with VerticalScroll():
			# with Horizontal(classes="runner-status-section"):
			# 	yield Label("Positions")
			# 	yield Label(" ", id="runner-update-open-option-positions-active", classes="active-label")
			# 	yield Label(" ", id="runner-update-open-option-positions-status", classes="status-label")

			# with Horizontal(classes="runner-status-section"):
			# 	yield Label("Market")
			# 	yield Label(" ", id="runner-update-open-option-positions-market-data-active", classes="active-label")
			# 	yield Label(" ", id="runner-update-open-option-positions-market-data-status", classes="status-label")

			with Horizontal(classes="runner-status-section"):
				yield Label("Broker Orders")
				yield Label(" ", id="runner-open-broker-option-orders-active", classes="active-label")
				yield Label(" ", id="runner-open-broker-option-orders-status", classes="status-label")
				yield Label(" ", id="runner-open-broker-option-orders-epoch", classes="status-label")

			# with Horizontal(classes="runner-status-section"):
			# 	yield Label("Broker Orders Market Data")
			# 	yield Label(" ", id="runner-broker-orders-market-data-active", classes="active-label")
			# 	yield Label(" ", id="runner-broker-orders-market-data-status", classes="status-label")

			# with Horizontal(classes="runner-status-section"):
			# 	yield Label("Trigger Market Data")
			# 	yield Label(" ", id="runner-trigger-market-data-active", classes="active-label")
			# 	yield Label(" ", id="runner-trigger-market-data-status", classes="status-label")

			# with Horizontal(classes="runner-status-section"):
			# 	yield Label("Trailing Orders")
			# 	yield Label(" ", id="runner-trailing-orders-active", classes="active-label")
			# 	yield Label(" ", id="runner-trailing-orders-status", classes="status-label")

			# with Horizontal(classes="runner-status-section"):
			# 	yield Label("Trailing Market Data")
			# 	yield Label(" ", id="runner-trailing-orders-market-data-active", classes="active-label")
			# 	yield Label(" ", id="runner-trailing-orders-market-data-status", classes="status-label")

			# with Horizontal(classes="runner-status-section"):
			# 	yield Label("Bracket Orders")
			# 	yield Label(" ", id="runner-bracket-orders-active", classes="active-label")
			# 	yield Label(" ", id="runner-bracket-orders-status", classes="status-label")

			# with Horizontal(classes="runner-status-section"):
			# 	yield Label("Bracket Market Data")
			# 	yield Label(" ", id="runner-bracket-orders-market-data-active", classes="active-label")
			# 	yield Label(" ", id="runner-bracket-orders-market-data-status", classes="status-label")

	def on_mount(self) -> None:
		self.set_interval(.25, self.refresh_data)

	def refresh_data(self) -> None:
		runners_status_list = database.get_all_runners_status()
		for runner_status in runners_status_list:
			active_label = self.query_one(
				f"#runner-{runner_status['runner_name_pk'].replace('_', '-')}-active", Label
			)
			status_label = self.query_one(
				f"#runner-{runner_status['runner_name_pk'].replace('_', '-')}-status", Label
			)
			epoch_label = self.query_one(
				f"#runner-{runner_status['runner_name_pk'].replace('_', '-')}-epoch", Label
			)

			if runner_status["active"] == True:
				active_label.styles.background = "green"
			else:
				active_label.styles.background = "red"

			runner_healthy = False
			if runner_status["current_update_success"] or runner_status["previous_update_success"]:
				runner_healthy = True

			if runner_healthy == True:
				status_label.styles.background = "green"
			else:
				status_label.styles.background = "red"

			now = time.time()
			last_update_limit = (float(runner_status["adjusted_interval"]) / 2) + float(runner_status["epoch_time_previous_success"])
			epoch_healthy = False
			if now <= last_update_limit:
				epoch_healthy = True

			if epoch_healthy == True:
				epoch_label.styles.background = "green"
			else:
				epoch_label.styles.background = "red"



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
