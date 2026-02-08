import time
import datetime
import json

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
		res = systemd.start_systemd_services()
		self.notify(str(res))

	@on(Button.Pressed, "#button-stop-runners")
	def handle_button_stop_runners_click(self) -> None:
		self.notify("button-stop-runners was clicked!")
		res = systemd.stop_systemd_services()
		self.notify(str(res))


	@on(Button.Pressed, "#button-install-runners")
	def handle_button_install_runners_click(self) -> None:
		self.notify("button-install-runners was clicked!")
		res = systemd.install_systemd_services(dest_dir="/etc/systemd/system", overwrite=True)
		self.notify(str(res))


	@on(Button.Pressed, "#button-remove-runners")
	def handle_button_remove_runners_click(self) -> None:
		self.notify("button-remove-runners was clicked!")
		res = systemd.remove_systemd_services()
		self.notify(str(res))


	@on(Button.Pressed, "#button-enable-runners")
	def handle_button_enable_runners_click(self) -> None:
		self.notify("button-enable-runners was clicked!")
		res = systemd.enable_systemd_services()
		self.notify(str(res))


	@on(Button.Pressed, "#button-disable-runners")
	def handle_button_disable_runners_click(self) -> None:
		self.notify("button-disable-runners was clicked!")
		res = systemd.disable_systemd_services()
		self.notify(str(res))


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
		self.set_interval(2, self.refresh_data)

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
				#status_label.refresh()
			else:
				status_label.styles.background = "red"
				#status_label.refresh()

			now = database.get_rounded_epoch_time()
			now_est = datetime.datetime.fromtimestamp(now).strftime("%d/%m/%Y, %H:%M:%S")
			interval = float(runner_status["adjusted_interval"])
			previous_update_time = float(runner_status["epoch_time_previous_success"])
			previous_update_est = datetime.datetime.fromtimestamp(previous_update_time).strftime("%d/%m/%Y, %H:%M:%S")
			epoch_healthy = False
			self.notify(f"now_est: {now_est}\nprev upd est: {previous_update_est}\nprev update: {str(previous_update_time)}\ninterval: {interval}\nnow - previous_update: {str(now - previous_update_time)}")
			if interval >= (now - previous_update_time):
				epoch_healthy = True

			if epoch_healthy == True:
				epoch_label.styles.background = "green"
				#epoch_label.refresh(recompose=True)
			else:
				epoch_label.styles.background = "red"
				#epoch_label.refresh(recompose=True)

		self.refresh()


class DataTablePositions(DataTable):
	def on_mount(self) -> None:
		"""Set up the data table and start auto-refresh."""
		# table = self.query_one("#positions-table", DataTable)
		self.cursor_type = "row"
		self.zebra_stripes = True

		# Add columns
		self.add_column("ID", key="id", width=2)
		self.add_column("position_description", width=30)
		# self.add_column("Symbol", key="symbol", width=8)
		# self.add_column("Type", key="type", width=6)
		# self.add_column("Strike", key="strike", width=10)
		# self.add_column("Expiry", key="expiry", width=12)
		# self.add_column("Qty", key="qty", width=6)
		# self.add_column("Avg Price", key="avg_price", width=12)
		# self.add_column("Current", key="current", width=12)
		# self.add_column("P/L", key="pl", width=12)
		# self.add_column("P/L %", key="pl_pct", width=10)

		# Load initial data
		# self.refresh_data()

		# Start auto-refresh
		# self.set_interval(self.refresh_interval, self.refresh_data)

	def refresh_data(self) -> None:
		positions = database.get_all_from_table("open_option_positions")
		market_data_list = database.get_all_from_table("open_option_positions_market_data")

		# Build lookup dict for market data by option_id
		market_data_lookup = {}
		for market_data in market_data_list:
			json_data = market_data.get("json_data", {})
			if isinstance(json_data, str):
				json_data = json.loads(json_data)
			option_id = json_data.get("instrument_id", "")
			if option_id:
				market_data_lookup[option_id] = json_data

		# Clear existing rows
		self.clear()

		# Populate table with position data
		if positions:
			for position in positions:
				local_id = position.get("local_id")
				json_data = position.get("json_data")

				# Parse JSON data if it's a string
				if isinstance(json_data, str):
					json_data = json.loads(json_data)

				# Extract position details
				symbol = json_data.get("chain_symbol")
				position_type = json_data.get("type")  # long or short
				option_id = json_data.get("option_id")
				quantity = float(json_data.get("quantity"))
				avg_price = float(json_data.get("average_price"))
				expiry = json_data.get("expiration_date")

				# Get market data for this position
				current_price = 0.0
				option_type = ""
				strike_price = 0.0

				if option_id in market_data_lookup:
					market_data = market_data_lookup[option_id]
					current_price = float(market_data.get("mark_price", 0))
					option_type = market_data.get("type", "")  # call or put
					strike_price = float(market_data.get("strike_price", 0))

				# Calculate P/L %
				profit_loss_pct = 0.0
				if avg_price > 0:
					profit_loss_pct = ((current_price - avg_price) / avg_price) * 100

				# Format compact description
				# Format: IWM P 263.0 1/20 x1 @39.00→38.00 +2.5%
				expiry_short = expiry[-5:] if len(expiry) >= 5 else expiry  # MM/DD format
				pl_sign = "+" if profit_loss_pct >= 0 else ""
				position_description = (
					f"{symbol} {option_type.upper()[0] if option_type else '?'} {strike_price:.2f} "
					f"{expiry_short} x{int(quantity)} @{avg_price:.2f}→{current_price:.2f} "
					f"{pl_sign}{profit_loss_pct:.1f}%"
				)

				# Add row to table
				self.add_row(str(local_id), position_description, key=str(local_id))






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
